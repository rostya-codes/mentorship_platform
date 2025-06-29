import csv
import secrets
from datetime import datetime, timedelta

from django.contrib.auth import authenticate, get_user_model
from django.http import HttpResponse
from django.utils import timezone

from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from api.permissions import IsMentor, IsSuperUser
from api.serializers import (
    CreateReviewSerializer,
    CreateSlotSerializer,
    MentorsRatingSerializer,
    ReviewSerializer,
    SlotBookSerializer,
    SlotSerializer,
    UserBlockUnblockSerializer,
    UserProfileSerializer,
    UserSerializer,
)
from api.tasks import send_password_reset
from reviews.models import Review
from schedule.models import Slot

from .exceptions import (
    CannotLeaveBefore,
    NotYourSlot,
    ReviewAlreadyExists,
    SlotDoesNotExist,
    TooBigComment,
    TooSmallStars,
    UnsupportedStarsAmount,
)

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
        method='get',
        responses={200: ReviewSerializer(many=True)},
        operation_summary='View all mentor\'s reviews'
    )
    @action(detail=True, methods=['get'], url_path='mentors_reviews')
    def mentors_reviews(self, request, pk=None):
        user = self.get_object()
        reviews = Review.objects.filter(mentor=user)
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        method='get',
        responses={200: SlotSerializer(many=True)},
        operation_summary='View all free mentor\'s slots'
    )
    @action(detail=True, methods=['get'], url_path='free_mentors_slots')
    def free_mentors_slots(self, request, pk=None):
        user = self.get_object()
        slots = Slot.objects.filter(user=user, is_booked=False)
        serializer = SlotSerializer(slots, many=True)  # many=True обов'язково
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        method='get',
        responses={200: MentorsRatingSerializer()},
        operation_summary='View mentor\'s average rating and review count'
    )
    @action(detail=True, methods=['get'], url_path='rating')
    def rating(self, request, pk=None):
        """
        Посмотреть средний рейтинг ментора
            Endpoint возвращает средний рейтинг и количество отзывов по ментору.
        """
        mentor = self.get_object()
        average_rating = mentor.get_average_rating()
        reviews_count = Review.objects.filter(mentor=mentor).count()
        data = {'average_rating': average_rating, 'reviews_count': reviews_count}
        serializer = MentorsRatingSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)


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
        responses={201: CreateReviewSerializer()},
        operation_summary='Leave review for booked and ended slot.'
    )
    @action(detail=True, methods=['post'], url_path='review')
    def leave_review(self, request, pk=None):
        user = request.user
        slot = self.get_object()

        serializer = CreateReviewSerializer(data=request.data, context={'request': request, 'slot': slot})
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save(mentor=slot.mentor, slot=slot, user=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except SlotDoesNotExist as exc:
            return Response({'error': str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except ReviewAlreadyExists as exc:
            return Response({'error': str(exc)}, status=status.HTTP_409_CONFLICT)
        except NotYourSlot as exc:
            return Response({'error': str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except CannotLeaveBefore as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except TooSmallStars as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except TooBigComment as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except UnsupportedStarsAmount as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except serializers.ValidationError as exc:
            return Response({'error': exc.detail}, status=status.HTTP_400_BAD_REQUEST)
    @swagger_auto_schema(
        method='get',
        responses={200: SlotSerializer(many=True)},
        operation_summary='View all my bookings'
    )
    @action(detail=False, methods=['get'], url_path='my')
    def my_bookings(self, request, pk=None):
        user = request.user
        slots = Slot.objects.filter(user=user)
        serializer = SlotSerializer(slots, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


    # @swagger_auto_schema(
    #     method='get',
    #     responses={200: }
    # )


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer

    def destroy(self, request, *args, **kwargs):
        review = self.get_object()
        now = timezone.now()
        if now > review.created_at + timedelta(days=1):
            return Response({'error': 'You have only 24 hours to delete your review and this time has expired.'},
                            status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """вызывается только для PUT"""
        partial = kwargs.get('partial', False)
        print(partial)
        review = self.get_object()
        now = timezone.now()
        if now > review.created_at + timedelta(days=1):
            return Response({'error': 'You have only 24 hours to update your review and this time has expired.'},
                            status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)


class AuthViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['post'], url_path='token')
    def obtain_token(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username)
        if user is not None:
            refresh = RefreshToken.for_user(user)
            data = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'email': user.email,
                'first_name': user.first_name,
            }
            return Response(data, status=status.HTTP_200_OK)
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


class ProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        responses={200: UserProfileSerializer()},
    )
    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=UserProfileSerializer(),
        responses={200: UserProfileSerializer()},
    )
    def put(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CreateSlotAPIView(APIView):
    permission_classes = [IsMentor, IsAuthenticated]

    @swagger_auto_schema(
        request_body=CreateSlotSerializer(),
        responses={200: CreateSlotSerializer()},
        operation_summary='Create slot api view'
    )
    def post(self, request):
        serializer = CreateSlotSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(mentor=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UsersStatsAPIView(APIView):
    permission_classes = [IsSuperUser]

    @swagger_auto_schema(operation_summary='User stats api view only for superusers')
    def get(self, request):
        total_users = User.objects.all().count()
        active_users = User.objects.filter(is_active=True).count()
        staff_users = User.objects.filter(is_staff=True).count()
        superusers = User.objects.filter(is_superuser=True).count()

        data = {
            "total_users": total_users,
            "active_users": active_users,
            "staff_users": staff_users,
            "superusers": superusers
        }
        return Response(data, status=status.HTTP_200_OK)


class UserBlockUnblockAPIView(APIView):
    permission_classes = [IsAdminUser]

    @swagger_auto_schema(
        request_body=UserBlockUnblockSerializer(),
        responses={200: UserBlockUnblockSerializer()},
        operation_summary='Block or unblock user using id',
    )
    def post(self, request):
        serializer = UserBlockUnblockSerializer(data=request.data)
        if serializer.is_valid():
            user_id = serializer.validated_data['id']
            block = serializer.validated_data['block']
            try:
                user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
            if block:
                user.is_active = False
                user.blocked_until = datetime.now() + timedelta(days=7)
                user.last_unblocked = None
            else:
                user.is_active = True
                user.last_unblocked = datetime.now()
                user.blocked_until = None
            user.save()
            return Response(UserBlockUnblockSerializer(user).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogsAPIView(APIView):

    permission_classes = [IsSuperUser]

    @swagger_auto_schema(
        operation_summary='Get logs'
    )
    def get(self, request):
        with open('request_logs.log', 'r', encoding='utf-8') as file:
            text = file.read()
        return Response({'text': text})


class UserExportCSVAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        users = User.objects.all()

        # Создаём HTTP-ответ с правильными заголовками
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="users_export.csv"'

        writer = csv.writer(response)
        header = ['id', 'username', 'email',
                  'first_name', 'last_name', 'is_active',
                  'is_email_verified', 'phone_number', 'image',
                  'is_mentor', 'is_staff', 'blocked_until',
                  'last_unblocked', 'last_active_time']

        writer.writerow(header)

        for user in users:
            writer.writerow([
                user.id,
                user.username,
                user.email,
                user.first_name,
                user.last_name,
                user.is_active,
                user.is_email_verified,
                user.phone_number,
                user.image,
                user.is_mentor,
                user.is_staff,
                user.blocked_until,
                user.last_unblocked,
                user.last_active_time
            ])
        return response


class ResetPasswordAPIView(APIView):
    def post(self, request):
        user_id = request.user.id
        if not user_id:
            return Response({'error': 'Missing user id.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Генерируем временный пароль (например, 12 символов)
        temp_password = secrets.token_urlsafe(9)

        # Сброс пароля
        user.set_password(temp_password)
        user.save()

        send_password_reset.delay(user_email=user.email, temp_password=temp_password)

        return Response({
            'message': 'Password has been reset.',
            'temporary_password': temp_password,
            'user_id': user.id,
        }, status=status.HTTP_200_OK)

