from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver

from reviews.models import Review


@receiver(post_save, sender=Review)
def send_email_to_mentor_review(sender, instance, created, **kwargs):
    if created and instance.mentor.email:
        subject = "You've received a new review!"
        message = (
            f"Hello {instance.mentor.get_full_name()},\n\n"
            f"You have received a new review from {instance.user.get_full_name() if instance.user else 'an anonymous user'}.\n\n"
            f"Rating: {instance.rating} out of 5\n"
            f"Comment: {instance.comment}\n\n"
            f"Best regards,\n"
            f"Your team"
        )
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [instance.mentor.email],
            fail_silently=True  # Set to False if you want to see errors while testing
        )
