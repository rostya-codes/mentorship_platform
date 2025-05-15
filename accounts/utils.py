from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

token_generator = PasswordResetTokenGenerator()


def generate_token(user):
    return token_generator.make_token(user)


def verify_token(user, token):
    return token_generator.check_token(user, token)


def encode_uid(user):
    return urlsafe_base64_encode(force_bytes(user.pk))


def decode_uid(uidb64):
    try:
        return force_str(urlsafe_base64_decode(uidb64))
    except Exception:
        return None
