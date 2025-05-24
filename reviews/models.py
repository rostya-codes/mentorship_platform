from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import ForeignKey


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
        return f'{self.pk} M: {self.mentor.username} U: {self.user.username}'
