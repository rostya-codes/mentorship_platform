import json

from django.template.loader import render_to_string

from asgiref.sync import sync_to_async
from channels.exceptions import DenyConnection
from channels.generic.websocket import AsyncWebsocketConsumer

from chat.models import Chatroom, Message


class ChatConsumer(AsyncWebsocketConsumer):
    """ Main chat messages async consumer """

    async def connect(self):
        self.user = self.scope['user']
        self.chatroom_unique_name = self.scope['url_route']['kwargs']['room_name']

        try:
            self.chatroom= await sync_to_async(Chatroom.objects.get)(unique_name=self.chatroom_unique_name)
        except Chatroom.DoesNotExist:
            raise DenyConnection('Chatroom does not exist')

        # Присоединяемся к группе
        await self.channel_layer.group_add(
            self.chatroom_unique_name, self.channel_name
        )

        if hasattr(self.user, 'is_authenticated') and self.user.is_authenticated:
            users_online = await sync_to_async(lambda: list(self.chatroom.users_online.all()))()
            if self.user not in users_online:
                await sync_to_async(self.chatroom.users_online.add)(self.user)

        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.chatroom_unique_name, self.channel_name)

        users_online = await sync_to_async(lambda: list(self.chatroom.users_online.all()))()
        if self.user in users_online:
            await sync_to_async(self.chatroom.users_online.remove)(self.user)

    async def receive(self, text_data=None):
        data = json.loads(text_data)
        body = data['body']
        message = await sync_to_async(Message.objects.create)(body=body, author=self.user, chat=self.chatroom)
        print("Received data:", data)
        print("User:", self.user)
        print("Chatroom:", self.chatroom)
        event = {
            'type': 'message_handler',
            'message_id': message.id,
        }
        await self.channel_layer.group_send(self.chatroom_unique_name, event)

    async def message_handler(self, event):
        message_id = event['message_id']
        message = await sync_to_async(Message.objects.get)(pk=message_id)
        context = {
            'user': self.user,
            'message': message,
            'chatroom': self.chatroom,
        }
        html = await sync_to_async(render_to_string)(
            'chat/partials/chat-message-p.html', context=context
        )
        await self.send(text_data=json.dumps({
            'body': html,
            'target': '#chat_messages',
            'swap': 'beforeend'
        }))


class OnlineStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        # тут логіка онлайна

    async def disconnect(self, close_code):
        # тут логіка при виході
        pass
