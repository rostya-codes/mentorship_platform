from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.db.models import Avg
from django.utils import timezone

from accounts.managers import CustomUserManager
from reviews.models import Review


class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(
        max_length=30,
        unique=True,
        verbose_name="Username"
    )

    first_name = models.CharField(
        max_length=64,
        verbose_name="First Name"
    )

    last_name = models.CharField(
        max_length=64,
        verbose_name="Last Name"
    )

    email = models.EmailField(
        unique=True,
        verbose_name="Email Address"
    )

    is_email_verified = models.BooleanField(default=False)

    phone_number = models.CharField(
        unique=True,
        blank=True,
        null=True,
        verbose_name="Phone Number"
    )

    image = models.ImageField(upload_to='accounts_images', null=True, blank=True)

    is_mentor = models.BooleanField(
        default=False,
        verbose_name="Is Mentor"
    )

    is_staff = models.BooleanField(
        default=False,
        verbose_name="Is Staff"
    )

    is_active = models.BooleanField(default=True)
    blocked_until = models.DateTimeField(null=True, blank=True)
    last_unblocked = models.DateTimeField(null=True, blank=True)

    last_active_time = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    objects = CustomUserManager()

    def __str__(self):
        return f'{self.pk} {self.username}'

    def is_blocked(self):
        if self.blocked_until and self.blocked_until > timezone.now():
            return True
        return not self.is_active

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_average_rating(self):
        avg = Review.objects.filter(mentor=self).aggregate(Avg('rating'))['rating__avg'] or 0
        return round(float(avg), 2)
