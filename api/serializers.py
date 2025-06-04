from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import AuthUser, TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import Token

from common.validators import validate_review_logic
from reviews.models import Review
from schedule.models import Slot

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

        try:
            validate_review_logic(user, slot, rating, comment)
        except ValidationError as exc:
            raise serializers.ValidationError(str(exc))

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
