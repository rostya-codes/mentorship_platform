from django.core.exceptions import ValidationError


def validate_slot_logic(is_booked, user):
    if (is_booked and not user) or (not is_booked and user):
        raise ValidationError('is_booked and user existing is connected fields.')
