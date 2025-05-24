from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.serializer import UserSerializer, ReviewSerializer, SlotSerializer, SlotBookSerializer, CreateReviewSerializer
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
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        method='post',
        responses={200: ReviewSerializer()},
        operation_summary='View all mentor\'s reviews'
    )
    @action(detail=True, methods=['get'], url_path='reviews')
    def reviews(self, request):
        user = self.get_object()
        reviews = Review.objects.filter(mentor=user)
        serializer = ReviewSerializer(reviews, many=True)
        return Response({serializer.data}, status=status.HTTP_200_OK)


class SlotViewSet(viewsets.ModelViewSet):
    queryset = Slot.objects.all()
    serializer_class = SlotSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        method='post',
        request_body=SlotBookSerializer(),
        responses={200: SlotSerializer()},
    )
    @action(detail=True, methods=['post'], url_path='book')
    def book(self, request, pk=None):
        slot = self.get_object()
        user = request.user

        if slot.is_booked:
            return Response({'error': 'Slot already booked.'}, status=status.HTTP_400_BAD_REQUEST)
        slot.user = user
        slot.is_booked = True
        slot.save()

        serializer = SlotSerializer(slot)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        method='post',
        responses={200: SlotSerializer(),}
    )
    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        slot = self.get_object()
        user = request.user

        if slot.user != user:
            return Response({'error': 'You can only apply your own bookings.'}, status=status.HTTP_403_FORBIDDEN)

        slot.user = None
        slot.is_booked = False
        slot.save()

        serializer = SlotSerializer(slot)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        method='post',
        request_body=CreateReviewSerializer,
        responses={201: CreateReviewSerializer(),}
    )
    @action(detail=True, methods=['post'], url_path='review')
    def leave_review(self, request, pk=None):
        user = request.user
        slot = self.get_object()

        if slot.user == user:
            if slot.is_booked:
                if not Review.objects.filter(user=user, slot=slot).exists():

                    serializer = CreateReviewSerializer(data=request.data)
                    if serializer.is_valid():
                        serializer.save(mentor=slot.mentor, user=user, slot=slot)
                        return Response(serializer.data, status=status.HTTP_201_CREATED)
                    return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
                return Response({'error': 'Review already exists.'}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'error': 'Slot is not booked.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'error': 'Slot is not yours.'}, status=status.HTTP_403_FORBIDDEN)

    @swagger_auto_schema(
        method='get',
        responses={200: SlotSerializer(many=True)},
        operation_summary='View all my bookings'
    )
    @action(detail=False, methods=['get'], url_path='my')
    def my_bookings(self, request):
        user = request.user
        slots = Slot.objects.filter(user=user)
        serializer = SlotSerializer(slots, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer

