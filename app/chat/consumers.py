import asyncio
import os
import aiohttp
import redis.asyncio as aioredis 
import json
from urllib.parse import parse_qs
from typing import NoReturn

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

logger: logging.Logger = logging.getLogger(name=__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self) -> None:
        connected_user: Any = self.scope["user"]
        self.room_name: str = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name: str = "chat_%s" % self.room_name
        try:
            self.room: ChatRoom = await database_sync_to_async(ChatRoom.objects.get)(pk=self.room_name)
        except ChatRoom.DoesNotExist:
            logger.error(msg=f"Chat room with ID {self.room_name} does not exist.")
            await self.close()
            return
        except Exception as e:
            logger.error(msg=f'Room init error: {e}')
            await self.close()
            return

        if connected_user not in await database_sync_to_async(list)(
            self.room.members.all()
        ):
            raise PermissionDenied("You are not allowed to access this chat room.")
        
        self.user_id: str = str(object=self.scope["user"].id)
        
        self.redis: aioredis.Redis = aioredis.Redis(
            host=os.getenv(key='REDIS_HOST'),
            port=os.getenv(key='REDIS_PORT'),
            # password=os.getenv('REDIS_PASSWORD'),
            db=0,
            encoding="utf-8",
            decode_responses=True
        )

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        asyncio.create_task(coro=self.safe_task(coro=self.init()))
        asyncio.create_task(coro=self.safe_task(coro=self.check_timeout()))
        asyncio.create_task(coro=self.safe_task(coro=self.event_push()))

    async def disconnect(self, close_code: int) -> None:
        await self.redis.close()
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def init(self) -> None:
        self.last_ping_time: datetime = datetime.now()
        self.language: str = parse_qs(qs=self.scope["query_string"].decode("utf8")).get('lang', ['en'])[0]

    async def send_pong(self) -> NoReturn:
        while True:
            await asyncio.sleep(delay=10)
            await self.send(text_data=json.dumps(obj={'type': 'pong'}))

    async def check_timeout(self) -> None:
        timeout: timedelta = timedelta(minutes=5)
        while True:
            await asyncio.sleep(delay=10)
            if datetime.now() - self.last_ping_time > timeout:
                logger.warning(msg=f"No Ping received from user_{self.user_id} for 5 minutes, disconnecting...")
                await self.close()
                break

    async def receive(self, text_data: str) -> None:
        try:
            json_data: dict = json.loads(s=text_data)
        except json.JSONDecodeError:
            json_data = dict()
        
        if json_data.get('type') == 'ping':
            self.last_ping_time: datetime = datetime.now()
            await self.send(text_data=json.dumps(obj={'type': 'pong'}))
            return
        
        if json_data.get('type') == 'lang' and json_data.get('data', '') in ['en', 'zh']:
            self.language = json_data['data']
            await self.send(text_data=json.dumps(obj={'type': 'lang', 'data': self.language}))
            return

        # room: ChatRoom = await database_sync_to_async(ChatRoom.objects.get)(pk=self.room_name)

        message_obj: Message = Message(user=self.scope["user"], content=text_data, room=self.room)
        await sync_to_async(func=message_obj.save)()

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": text_data,
                "user_id": self.user_id,
            },
        )

    async def chat_message(self, event: dict) -> None:
        message: Any = event["message"]
        try:
            message: dict = json.loads(s=message)
        except:
            pass
        
        await self.send(text_data=json.dumps(obj={"type": "message", "data": message, "user_id": self.user_id}, ensure_ascii=False))

    async def safe_task(self, coro: Any) -> None:
        try:
            await coro
        except Exception as e:
            logger.error(msg=f"Uncaught exception: {e}")

    async def get_subscriptions(self) -> list[UserSubscription] | None:
        cache_key: str = f'satoshi:subscriptions:{self.user_id}'
        subscriptions: list[UserSubscription] | None = cache.get(key=cache_key)
        if not subscriptions:
            subscriptions: list[UserSubscription] = await database_sync_to_async(list)(UserSubscription.objects.filter(user_id=self.user_id))
            cache.set(key=cache_key, value=subscriptions, timeout=60)
        return subscriptions

    async def event_push(self) -> NoReturn:
        while True:
            try:
                subscriptions: list[UserSubscription] | None = await self.get_subscriptions()
                if subscriptions:
                    subscriptions_dict: dict = {}
                    for subscription in subscriptions:
                        if subscription.message_type == 3:
                            content: dict[str, Any] = {c['address'].lower():c.get('name', c['address'][-4:]) for c in subscription.content}
                        else:
                            content: Any = subscription.content
                        subscriptions_dict[MESSAGE_TYPE_DICT[subscription.message_type]] = content

                    data: list[dict] = await self.get_event(subscriptions_dict=subscriptions_dict)

                    new_data: list = []
                    for news in data:
                        feed_id: str = f"{news['data_type']}_{news['id']}"
                        key: str = f'satoshi:feed:{self.user_id}:{feed_id}'
                        
                        if not await self.redis.exists(key):
                            await self.redis.set(name=key, value=1, ex=86400)
                            new_data.append(news)
                   
                    if new_data:
                        await self.send(text_data=json.dumps(obj={"type": "event", "data": new_data}, ensure_ascii=False))
            except Exception as e:
                logger.error(msg=f'Event push: {e}')
            finally:
                await asyncio.sleep(delay=3)

    async def get_event(self, subscriptions_dict) -> list[dict]:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=120)) as session:
            url: str = f"{os.getenv(key='SUB_API')}/message_post/"
            response_json: dict = await self.fetch(session=session, url=url, data=dict(user_id=self.user_id, language=self.language, content=subscriptions_dict))

        data: list[dict] = response_json.get('data', [])
        return data

    async def fetch(self, session: aiohttp.ClientSession, url: str, data: dict) -> dict:
        async with session.get(url=url, json=data) as response:
            return await response.json()
