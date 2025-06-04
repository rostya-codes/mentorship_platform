from django.contrib.auth import get_user_model, authenticate
from django.core.exceptions import ValidationError

User = get_user_model()


def validate_register_logic(username):
    if ' ' in username:
        raise ValidationError('Username cannot contain spaces.')
    if not username.strip():
        raise ValidationError("Username cannot be empty or contain only spaces.")
    return username


def validate_login_logic(username_or_email, password, instance):

    if username_or_email and password:
        # Пытаемся найти пользователя по email или username
        try:
            user = User.objects.get(email=username_or_email)
            username = user.username  # конвертируем email → username
        except User.DoesNotExist:
            username = username_or_email

        instance.user_cache = authenticate(instance.request, username=username, password=password)

        if instance.user_cache is None:
            raise ValidationError("Invalid login credentials")
        else:
            instance.confirm_login_allowed(instance.user_cache)

    return instance.cleaned_data
