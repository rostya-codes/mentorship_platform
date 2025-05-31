from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView
)


router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'slots', views.SlotViewSet)
router.register(r'reviews', views.ReviewViewSet)
router.register(r'auth', views.AuthViewSet, basename='auth')

urlpatterns = [
    path('', include(router.urls)),
    path('token/', TokenObtainPairView.as_view(), name='token-obtain-pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('profile/', views.ProfileAPIView.as_view(), name='profile-api-view'),
    path('create-slot/', views.CreateSlotAPIView.as_view(), name='create-slot-api-view'),
    path('users-stats/', views.UsersStatsAPIView.as_view(), name='users-stats-api-view'),
    path('user-block-unblock/', views.UserBlockUnblockAPIView.as_view(), name='user-block-unblock-api-view'),
    path('logs', views.LogsAPIView.as_view(), name='logs-api-view'),
    path('user-export-csv/', views.UserExportCSVAPIView.as_view(), name='user-export-csv-api-view'),
    path('reset-password/', views.ResetPasswordAPIView.as_view(), name='reset-password-api-view')
]
