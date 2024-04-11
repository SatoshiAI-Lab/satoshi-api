import asyncio
import os
import aiohttp
import json

from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import ChatRoom, Message
from django.core.exceptions import PermissionDenied
from datetime import datetime, timedelta
from subscribe.models import UserSubscription
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
        
        self.language = self.scope['url_route']['kwargs'].get('lang', 'en')

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        self.last_ping_time = datetime.now()
        asyncio.create_task(self.send_pong())
        asyncio.create_task(self.check_timeout())
        asyncio.create_task(self.event_push())

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def send_pong(self):
        while True:
            await asyncio.sleep(10)
            await self.send(json.dumps({'type': 'pong'}))

    async def check_timeout(self):
        timeout = timedelta(minutes=5)
        while True:
            await asyncio.sleep(10)
            if datetime.now() - self.last_ping_time > timeout:
                logger.warning("No Ping received for 5 minutes, disconnecting...")
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

        self.user_id = self.scope["user"].id
        room = await database_sync_to_async(ChatRoom.objects.get)(pk=self.room_name)

        message_obj = Message(user=self.scope["user"], content=text_data, room=room)
        await sync_to_async(message_obj.save)()

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": text_data,
                "user_id": str(self.user_id),
            },
        )

    async def chat_message(self, event):
        connected_user_model = self.scope["user"]
        user_id = str(connected_user_model.id)
        message = event["message"]
        try:
            message = json.loads(message)
        except:
            pass
        
        await self.send(text_data=json.dumps({"type": "message", "data": message, "user_id": user_id}, ensure_ascii=False))

    async def event_push(self):
        user_id = str(self.scope["user"].id)

        sent_data = set()
        while True:
            try:
                subscriptions = await database_sync_to_async(list)(UserSubscription.objects.filter(user_id=user_id))
                if subscriptions:
                    subscriptions_dict = {}
                    for subscription in subscriptions:
                        if subscription.message_type == 3:
                            content = {c['address']:c['name'] for c in subscription.content}
                        else:
                            content = subscription.content
                        subscriptions_dict[MESSAGE_TYPE_DICT[subscription.message_type]] = content

                    data = await self.get_event(user_id, subscriptions_dict)

                    new_data = [news for news in data if news["id"] not in sent_data]   
                    sent_data.update([news["id"] for news in new_data])
                    if new_data:
                        await self.send(text_data=json.dumps({"type": "event", "data": new_data}, ensure_ascii=False))

                    # if data:
                    #     await self.send(text_data=json.dumps({"type": "event", "data": data}, ensure_ascii=False))
                    #     await asyncio.sleep(10)
                    # await asyncio.sleep(30)
            except Exception as e:
                logger.error(f'Get event error: {e}')
            finally:
                await asyncio.sleep(3)


    async def get_event(self, user_id, subscriptions_dict):
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(120)) as session:
            url = f"{os.getenv('SUB_API')}/message_post"
            response_text = await self.fetch(session, url, dict(user_id=user_id, language=self.language, content=subscriptions_dict))

        data = json.loads(response_text).get('data', [])
        return data

    async def fetch(self, session, url, data):
        async with session.get(url, json=data) as response:
            return await response.text()
