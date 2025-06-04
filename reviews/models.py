from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import ForeignKey
from django.utils import timezone

from common.validators import validate_review_logic


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
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'{self.pk} M: {self.mentor.username} U: {self.user.username} | stars: {self.rating}'

    def clean(self):
        validate_review_logic(
            user=self.user,
            slot=self.slot,
            rating=self.rating,
            comment=self.comment,
            instance=self
        )
