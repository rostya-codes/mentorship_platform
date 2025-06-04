from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail


@shared_task
def send_password_reset(user_email, temp_password):
    subject = 'Password reset'
    message = ('Your password has been reset. Your new password below:\n'
               f'{temp_password}')
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user_email])
