from django.conf import settings
from django.db import models

import shortuuid


class Chatroom(models.Model):
    unique_name = models.CharField(max_length=128, unique=True, default=shortuuid.uuid)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='chats')
    users_online = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='users_online', blank=True)

    def __str__(self):
        return self.unique_name


class MyNotes(models.Model):
    unique_name = models.CharField(max_length=128, unique=True, default=shortuuid.uuid)
    owner = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)


class Message(models.Model):
    body = models.TextField(max_length=10000)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    chat = models.ForeignKey(Chatroom, related_name='chat_messages', on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        prefix = self.body[:100]
        if len(self.body) > 100:
            prefix += '...'
        return f'{self.author.username} : {prefix}'
