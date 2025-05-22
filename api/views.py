from django.contrib.auth import get_user_model
from django.shortcuts import render
from rest_framework import viewsets

from api.serializer import UserSerializer, ReviewSerializer, SlotSerializer
from reviews.models import Review
from schedule.models import Slot

User = get_user_model()


"""
Замість того, щоб писати окремі класи або методи для GET, POST, PUT, DELETE,
ти використовуєш один ViewSet, який сам розуміє, яку дію виконувати, залежно від запиту.
"""


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class SlotViewSet(viewsets.ModelViewSet):
    queryset = Slot.objects.all()
    serializer_class = SlotSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer



