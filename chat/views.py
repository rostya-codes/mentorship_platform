from django.contrib.auth import get_user_model
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from chat.forms import ChatMessageCreateForm
from chat.models import Chatroom

User = get_user_model()


class ChatView(View):
    def get(self, request, chatroom_unique_name=None):
        if not chatroom_unique_name:
            return redirect('index')

        chatroom = get_object_or_404(Chatroom, unique_name=chatroom_unique_name)
        chat_messages = chatroom.chat_messages.all()[:1000]  # Last 1000 messages
        form = ChatMessageCreateForm()

        other_user = None
        members = chatroom.members.all()
        if request.user not in members:
            raise Http404
        for member in members:
            if member != request.user:
                other_user = member
                break

        if request.htmx:
            form = ChatMessageCreateForm(request.POST)
            if form.is_valid():
                message = form.save(commit=False)
                message.author = request.user
                message.save()
                context = {
                    'message': message,
                    'user': request.user,
                }
                return render(request, 'chat/chat.html', context)

        context = {
            'chat_messages': chat_messages,
            'form': form,
            'other_user': other_user,
            'chatroom_unique_name': chatroom_unique_name,
            'chatroom': chatroom,
        }
        return render(request, 'chat/chat.html', context)


class StartChatView(View):
    def get(self, request, username):
        if request.user.username == username:
            return redirect('my-notes')

        other_user = User.objects.get(username=username)
        my_chatrooms = request.user.chats.all()
        if my_chatrooms.exists():
            for chatroom in my_chatrooms:
                if other_user in chatroom.members.all():
                    chatroom = chatroom
                    break
                else:
                    chatroom = Chatroom.objects.create()
                    chatroom.members.add(other_user, request.user)
        else:
            chatroom = Chatroom.objects.create()
            chatroom.members.add(other_user, request.user)

        return redirect('chatroom', chatroom.unique_name)


class MyNotesView(View):
    pass
