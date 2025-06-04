from datetime import datetime

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import ForeignKey
from django.utils import timezone


class Review(models.Model):
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=3
    )
    comment = models.TextField(max_length=1024, default='')
    mentor = ForeignKey(
        to='accounts.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='review_mentor'
    )
    user = ForeignKey(
        to='accounts.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='review_user'
    )
    slot = models.OneToOneField(
        to='schedule.Slot', on_delete=models.CASCADE,
        null=True, blank=True, related_name='review_slot'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.pk} M: {self.mentor.username} U: {self.user.username} | stars: {self.rating}'

    def clean(self):
        if 0 > self.rating > 5:
            raise ValidationError('Rating must be 0 - 5')

        if self.rating <= 2 and len(self.comment) < 15:
            raise ValidationError('Your rating is too small, you must write a comment (min 15 symbols)')

        review = Review.objects.filter(user=self.user, slot=self.slot).exclude(pk=self.pk)
        if review.exists():
            raise ValidationError('Your review for this slot already exists.')

        if self.slot:
            if not self.slot.user == self.user:
                raise ValidationError('You can only leave a review for a slot you attended.')

        now = timezone.now()
        event_datetime = datetime.combine(self.slot.date, self.slot.time)
        if timezone.is_aware(now):  # Add TIME_ZONE
            event_datetime = timezone.make_aware(event_datetime, timezone.get_current_timezone())
        if event_datetime > now:
            raise ValidationError('You cannot leave a review before the slot has ended.')
