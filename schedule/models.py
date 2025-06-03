from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.html import format_html


class Slot(models.Model):
    mentor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'is_mentor': True},
        related_name='mentor_slots'
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='user_bookings')
    date = models.DateField()
    time = models.TimeField()
    is_booked = models.BooleanField(default=False)

    class Meta:
        unique_together = ('mentor', 'date', 'time')

    def __str__(self):
        return f"{self.pk} {self.mentor.username} - {self.date} {self.time} ({'Booked' if self.is_booked else 'Free'})"

    def get_review_link(self):
        if hasattr(self, 'review_slot') and self.review_slot:
            return format_html(
            '<a href="/admin/reviews/review/{}/change/">Open review</a>', self.review_slot.id
        )
        return 'None'
    get_review_link.short_description = 'Review'

    def clean(self):
        if self.is_booked and not self.user or not self.is_booked and self.user:
            raise ValidationError('is_booked and user existing is connected fields.')


class BookingLog(models.Model):
    ACTION_CHOICES = (
        ('book', 'Booked'),
        ('cancel', 'Cancelled'),
    )

    user = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    slot = models.ForeignKey(to='Slot', on_delete=models.CASCADE)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} | action: {self.action}'
