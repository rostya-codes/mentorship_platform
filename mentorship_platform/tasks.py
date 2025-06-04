from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse


@shared_task
def send_booking_confirmation_email(user_email, user_first_name, mentor_name, date, time):
    subject = 'Slot Booked Successfully'
    my_bookings_url = f"{settings.SITE_DOMAIN}{reverse('my-bookings')}"  # Наприклад, https://mysite.com/accounts/my-bookings/
    print('send_booking_confirmation_email')
    message = (
        f"Hi {user_first_name},\n\n"
        f"Your slot with mentor {mentor_name} on {date} at {time} has been successfully booked.\n\n"
        f"You can view your bookings here: {my_bookings_url}\n\n"
        "Thank you for using our mentorship platform!"
    )

    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user_email])
