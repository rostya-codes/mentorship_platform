from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View

from chat.forms import ChatMessageCreateForm
from chat.models import Chatroom


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
