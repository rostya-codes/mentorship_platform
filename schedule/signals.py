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
