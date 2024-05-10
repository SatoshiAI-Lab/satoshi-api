import asyncio
import os
import aiohttp
import redis.asyncio as aioredis 
import json
from urllib.parse import parse_qs

from django.core.cache import cache

from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import ChatRoom, Message
from django.core.exceptions import PermissionDenied
from datetime import datetime, timedelta
from users.models import UserSubscription
from utils.constants import *

import logging

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        connected_user = self.scope["user"]
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = "chat_%s" % self.room_name
        try:
            self.room = await database_sync_to_async(ChatRoom.objects.get)(pk=self.room_name)
        except ChatRoom.DoesNotExist:
            logger.error(f"Chat room with ID {self.room_name} does not exist.")
            await self.close()
            return
        except Exception as e:
            logger.error(f'Room init error: {e}')
            await self.close()
            return

        if connected_user not in await database_sync_to_async(list)(
            self.room.members.all()
        ):
            raise PermissionDenied("You are not allowed to access this chat room.")
        
        self.user_id = str(self.scope["user"].id)
        
        self.redis = aioredis.Redis(
            host=os.getenv('REDIS_HOST'),
            port=os.getenv('REDIS_PORT'),
            # password=os.getenv('REDIS_PASSWORD'),
            db=0,
            encoding="utf-8",
            decode_responses=True
        )

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        asyncio.create_task(self.safe_task(self.init()))
        # asyncio.create_task(self.safe_task(self.send_pong()))
        asyncio.create_task(self.safe_task(self.check_timeout()))
        asyncio.create_task(self.safe_task(self.event_push()))

    async def disconnect(self, close_code):
        await self.redis.close()

        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def init(self):
        self.last_ping_time = datetime.now()
        self.language = parse_qs(self.scope["query_string"].decode("utf8")).get('lang', ['en'])[0]

    async def send_pong(self):
        while True:
            await asyncio.sleep(10)
            await self.send(json.dumps({'type': 'pong'}))

    async def check_timeout(self):
        timeout = timedelta(minutes=5)
        while True:
            await asyncio.sleep(10)
            if datetime.now() - self.last_ping_time > timeout:
                logger.warning(f"No Ping received from user_{self.user_id} for 5 minutes, disconnecting...")
                await self.close()
                break

    async def receive(self, text_data):
        try:
            json_data = json.loads(text_data)
        except json.JSONDecodeError:
            json_data = dict()
        
        if json_data.get('type') == 'ping':
            self.last_ping_time = datetime.now()
            await self.send(json.dumps({'type': 'pong'}))
            return
        
        if json_data.get('type') == 'lang' and json_data.get('data', '') in ['en', 'zh']:
            self.language = json_data['data']
            await self.send(json.dumps({'type': 'lang', 'data': self.language}))
            return

        room = await database_sync_to_async(ChatRoom.objects.get)(pk=self.room_name)

        message_obj = Message(user=self.scope["user"], content=text_data, room=room)
        await sync_to_async(message_obj.save)()

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": text_data,
                "user_id": self.user_id,
            },
        )

    async def chat_message(self, event):
        message = event["message"]
        try:
            message = json.loads(message)
        except:
            pass
        
        await self.send(text_data=json.dumps({"type": "message", "data": message, "user_id": self.user_id}, ensure_ascii=False))

    async def safe_task(self, coro):
        try:
            await coro
        except Exception as e:
            logger.error(f"Uncaught exception: {e}")

    async def get_subscriptions(self):
        cache_key = f'satoshi:subscriptions:{self.user_id}'
        subscriptions = cache.get(cache_key)
        if not subscriptions:
            subscriptions = await database_sync_to_async(list)(UserSubscription.objects.filter(user_id=self.user_id))
            cache.set(cache_key, subscriptions, timeout=60)
        return subscriptions

    async def event_push(self):
        while True:
            try:
                subscriptions = await self.get_subscriptions()
                if subscriptions:
                    subscriptions_dict = {}
                    for subscription in subscriptions:
                        if subscription.message_type == 3:
                            content = {c['address'].lower():c.get('name', c['address'][-4:]) for c in subscription.content}
                        else:
                            content = subscription.content
                        subscriptions_dict[MESSAGE_TYPE_DICT[subscription.message_type]] = content

                    data = await self.get_event(subscriptions_dict)

                    new_data = []
                    for news in data:
                        feed_id = f"{news['data_type']}_{news['id']}"
                        key = f'satoshi:feed:{self.user_id}:{feed_id}'
                        
                        if not await self.redis.exists(key):
                            await self.redis.set(key, 1, ex=86400)
                            new_data.append(news)
                   
                    if new_data:
                        await self.send(text_data=json.dumps({"type": "event", "data": new_data}, ensure_ascii=False))
            except Exception as e:
                logger.error(f'Event push: {e}')
            finally:
                await asyncio.sleep(3)

    async def get_event(self, subscriptions_dict):
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(120)) as session:
            url = f"{os.getenv('SUB_API')}/message_post/"
            response_text = await self.fetch(session, url, dict(user_id=self.user_id, language=self.language, content=subscriptions_dict))

        data = json.loads(response_text).get('data', [])
        return data

    async def fetch(self, session, url, data):
        async with session.get(url, json=data) as response:
            return await response.text()
