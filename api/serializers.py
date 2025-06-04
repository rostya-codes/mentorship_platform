from datetime import datetime
from django.utils import timezone

from django.contrib.auth import get_user_model

from rest_framework import serializers
from rest_framework_simplejwt.serializers import AuthUser, TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import Token

from reviews.models import Review
from schedule.models import Slot
from .exceptions import SlotDoesNotExist, ReviewAlreadyExists, NotYourSlot, CannotLeaveBefore, TooSmallStars, \
    TooBigComment, UnsupportedStarsAmount

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'


class UserBlockUnblockSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    block = serializers.BooleanField(default=False)
    is_active = serializers.BooleanField(read_only=True)
    blocked_until = serializers.DateTimeField(read_only=True)
    last_unblocked = serializers.DateTimeField(read_only=True)


class LogsSerializer(serializers.Serializer):
    text = serializers.CharField(read_only=True)


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class SlotSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = Slot
        fields = '__all__'


class CreateSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Slot
        fields = ['date', 'time', 'mentor']


class SlotBookSerializer(serializers.Serializer):
    slot_id = serializers.IntegerField()


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = '__all__'


class CreateReviewSerializer(serializers.ModelSerializer):

    class Meta:
        model = Review
        fields = ('rating', 'comment')

    def validate(self, attrs):
        slot = self.context.get('slot')
        user = self.context['request'].user
        rating = attrs.get('rating')
        comment = attrs.get('comment')

        if not slot:
            raise SlotDoesNotExist('Slot not provided to serializer context.')

        if Review.objects.filter(slot=slot, user=user).exists():
            raise ReviewAlreadyExists('Review already exists.')

        # проверяем, что пользователь — участник слота
        if user != slot.user:  # and user != slot.mentor
            raise NotYourSlot('You can only leave a review for a slot you participated in.')

        now = timezone.now()
        event_datetime = datetime.combine(slot.date, slot.time)
        if timezone.is_aware(now):
            event_datetime = timezone.make_aware(event_datetime, timezone.get_current_timezone())
        if event_datetime > now:
            raise CannotLeaveBefore('You cannot leave a review before the slot has ended.')

        if rating <= 2 and len(comment) < 15:
            raise TooSmallStars('If you give 2 or less stars, you should write why (min 15 symbols).')

        if len(comment) >= 1000:
            raise TooBigComment('Comment must contains max 1000 symbols.')

        if 1 > rating > 5:
            raise UnsupportedStarsAmount('Stars must be from 1 to 5.')

        return attrs

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user: AuthUser) -> Token:
        """
        Если расшифровать (декодировать) access-токен, внутри будет:
        {
            "token_type": "access",
            "exp": 1234567890,
            "jti": "...",
            "user_id": 1,
            "email": "user@example.com",
            "first_name": "Ivan"
        }
        """
        token = super().get_token(user)
        token['email'] = user.email
        token['first_name'] = user.first_name
        return token


class MentorsRatingSerializer(serializers.Serializer):
    average_rating = serializers.FloatField()
    reviews_count = serializers.IntegerField()
