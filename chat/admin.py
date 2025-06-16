from django.contrib import admin

from chat.models import Chatroom, Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'short_body', 'author', 'chat', 'created')
    list_filter = ('chat', 'author', 'created')
    search_fields = ('body', 'author__username', 'chat__unique_name')
    readonly_fields = ('created',)

    def short_body(self, obj):
        return obj.body[:40] + ('...' if len(obj.body) > 40 else '')
    short_body.short_description = "Body"

@admin.register(Chatroom)
class ChatroomAdmin(admin.ModelAdmin):
    list_display = ('id', 'unique_name', 'members_display')
    search_fields = ('unique_name',)
    filter_horizontal = ('members', 'users_online')

    def members_display(self, obj):
        return ", ".join([user.username for user in obj.members.all()])
    members_display.short_description = "Members"