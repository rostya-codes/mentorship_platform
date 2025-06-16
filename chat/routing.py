from django.urls import path

from .consumers import *

websocket_urlpatterns = [
    path('ws/chatroom/<str:room_name>', ChatConsumer.as_asgi()),
    path('ws/online-status/', OnlineStatusConsumer.as_asgi()),
]