from django.urls import path

from . import views

urlpatterns = [
    path('<str:username>', views.StartChatView.as_view(), name='start-chat'),
    path('room/<str:chatroom_unique_name>', views.ChatView.as_view(), name='chatroom'),
    path('my-notes/', views.MyNotesView.as_view(), name='my-notes')
]
