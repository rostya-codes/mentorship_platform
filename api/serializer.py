from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, AuthUser
from rest_framework_simplejwt.tokens import Token

from reviews.models import Review
from schedule.models import Slot

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class SlotSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = Slot
        fields = '__all__'


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
