from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Slot


@receiver(post_save, sender=Slot)
def log_slot_creation(sender, instance, created, **kwargs):
    if created:
        print(f"[SIGNAL] Новый слот создан! "
              f"ID: {instance.id}, "
              f"Ментор: {instance.mentor}, "
              f"Дата: {instance.date}, "
              f"Время: {instance.time}")


@receiver(post_save, sender=Slot)
def remind_user_about_slot(sender, instance, created, **kwargs):
    if instance.is_booked and instance.user:
        # Здесь обычная отправка сразу, для настоящей отложенной отправки — Celery/BackgroundTasks
        subject = "Your upcoming mentoring session reminder"
        message = (
            f"Hello {instance.user.get_full_name()},\n\n"
            f"This is a reminder about your upcoming session with mentor {instance.mentor.get_full_name()}.\n"
            f"Date: {instance.date}\n"
            f"Time: {instance.time}\n\n"
            f"Best regards,\nYour team"
        )
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [instance.user.email],
            fail_silently=True,
        )


# Test signal

# @receiver(signal=post_save, sender=User)
# def create_profile(sender, instance, created, **kwargs):
#     if created:
#         Profile.objects.create(user=instance)
