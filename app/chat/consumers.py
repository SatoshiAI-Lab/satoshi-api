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


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        connected_user = self.scope["user"]
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = "chat_%s" % self.room_name
        try:
            self.room = await database_sync_to_async(ChatRoom.objects.get)(
                pk=self.room_name
            )
        except:
            await self.close()
            return

        if connected_user not in await database_sync_to_async(list)(
            self.room.members.all()
        ):
            raise PermissionDenied("You are not allowed to access this chat room.")

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
                print("No Ping received for 5 minutes, disconnecting...")
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
        message = event["message"]
        user_id = str(connected_user_model.id)
        
        await self.send(text_data=json.dumps({"message": message, "user_id": user_id}))

    async def event_push(self):
        user_id = str(self.scope["user"].id)

        sent_data = set()
        while True:
            subscriptions = await database_sync_to_async(list)(UserSubscription.objects.filter(user_id=user_id))
            if not subscriptions:
                await asyncio.sleep(5)
                continue
            subscriptions_dict = {MESSAGE_TYPE_DICT[subscription.message_type]: subscription.content for subscription in subscriptions}

            async with aiohttp.ClientSession() as session:
                url = f"{os.getenv('SUB_API')}/message_post"
                response_text = await self.fetch(session, url, dict(user_id=user_id, language='en', content=subscriptions_dict))

            data = json.loads(response_text).get('data', [])
            new_data = [news for news in data if news["id"] not in sent_data]   
            sent_data.update([news["id"] for news in new_data])
            if new_data:
                await self.send(text_data=json.dumps({"type": "event", "data": new_data}, ensure_ascii=False))

            await asyncio.sleep(3)

    async def fetch(self, session, url, data):
        async with session.get(url, json=data) as response:
            return await response.text()