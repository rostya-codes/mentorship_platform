from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail

from celery import shared_task

User = get_user_model()


@shared_task
def register_email_confirm(user_id, verification_link):
    user = User.objects.get(pk=user_id)
    subject = 'Confirm your email'
    message = (f'Hi {user.username},\n\nPlease verify your account by clicking the link below:\n{verification_link}'
               f'\n\nThank you!')
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
