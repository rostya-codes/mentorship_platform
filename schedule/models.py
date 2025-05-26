from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Slot(models.Model):
    mentor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'is_mentor': True},
        related_name='mentor_slots'
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='user_bookings')
    date = models.DateField()
    time = models.TimeField()
    is_booked = models.BooleanField(default=False)

    class Meta:
        unique_together = ('mentor', 'date', 'time')

    def __str__(self):
        return f"{self.pk} {self.mentor.username} - {self.date} {self.time} ({'Booked' if self.is_booked else 'Free'})"


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
