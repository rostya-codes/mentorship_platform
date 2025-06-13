from django import forms

from chat.models import Message


class ChatMessageCreateForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ('body',)
        widgets = {
            'body': forms.TextInput(attrs={
                'placeholder': 'Aa',
                'class': 'p-4 text-blank',
                'maxlenght': '300',
                'autofocus': True
            }),
        }
