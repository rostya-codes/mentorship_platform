from datetime import datetime, timedelta

from django.utils import timezone
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Slot, BookingLog
from .tasks import remind_send_email_booking


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
        # Объединяем дату и время слота в один datetime
        slot_datetime = datetime.combine(instance.date, instance.time)
        slot_datetime = timezone.make_aware(slot_datetime, timezone.get_current_timezone())

        # Время отправки — за 1 час до встречи
        remind_at = slot_datetime - timedelta(hours=1)
        now = timezone.now()

        # Если время напоминания уже прошло, отправь сразу (на случай поздней брони)
        if remind_at < now:
            remind_send_email_booking.delay(
                user_full_name=instance.user.get_full_name(),
                mentor_full_name=instance.mentor.get_full_name(),
                date=instance.date,
                time=instance.time,
                email=instance.user.email,
            )
        else:
            # Иначе — планируем задачу на remind_at через eta
            remind_send_email_booking.apply_async(
                kwargs={
                    'user_full_name': instance.user.get_full_name(),
                    'mentor_full_name': instance.mentor.get_full_name(),
                    'date': instance.date,
                    'time': instance.time,
                    'email': instance.user.email,
                },
                eta=remind_at
            )


@receiver(post_save, sender=Slot)
def log_slot_booking(sender, instance, created, **kwargs):
    # Логируем бронирование
    if instance.is_booked and instance.user:
        if not BookingLog.objects.filter(user=instance.user, slot=instance,
                                         action='book').exists():
            BookingLog.objects.create(
                user=instance.user,
                slot=instance,
                action='book'
            )


# Test signal

# @receiver(signal=post_save, sender=User)
# def create_profile(sender, instance, created, **kwargs):
#     if created:
#         Profile.objects.create(user=instance)
