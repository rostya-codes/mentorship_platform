from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail


@shared_task
def remind_send_email_booking(user_full_name, mentor_full_name, date, time, email):
    subject = "Your upcoming mentoring session reminder"
    message = (
        f"Hello {user_full_name},\n\n"
        f"This is a reminder about your upcoming session with mentor {mentor_full_name}.\n"
        f"Date: {date}\n"
        f"Time: {time}\n\n"
        f"Best regards,\nYour team"
    )
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=True,
    )
