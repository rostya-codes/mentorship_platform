from datetime import datetime

from django.core.exceptions import ValidationError
from django.utils import timezone


def validate_review_logic(user, slot, rating, comment, instance=None):
    """
    Общая валидация для создания/обновления Review.
    instance — объект Review при обновлении (чтобы не ловить себя в exists)
    Генерирует ValidationError если что-то не так.
    """
    from reviews.models import Review

    if rating is not None and (rating < 1 or rating > 5):
        raise ValidationError('Rating must be 1 - 5')

    if rating is not None and rating <= 2 and (not comment or len(comment) < 15):
        raise ValidationError('If you give 2 or less stars, you should write why (min 15 symbols).')

    qs = Review.objects.filter(user=user, slot=slot)
    if instance:
        qs = qs.exclude(pk=instance.pk)
    if qs.exists():
        raise ValidationError('Your review for this slot already exists.')

    if slot and user != slot.user:
        raise ValidationError('You can only leave a review for a slot you participated in.')

    now = timezone.now()
    if slot:
        event_datetime = datetime.combine(slot.date, slot.time)
        if timezone.is_aware(now):
            event_datetime = timezone.make_aware(event_datetime, timezone.get_current_timezone())
        if event_datetime > now:
            raise ValidationError('You cannot leave a review before the slot has ended.')