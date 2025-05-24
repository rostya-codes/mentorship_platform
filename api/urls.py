from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . views import UserViewSet, SlotViewSet, ReviewViewSet
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView
)


router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'slots', SlotViewSet)
router.register(r'reviews', ReviewViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('token/', TokenObtainPairView.as_view(), name='token-obtain-pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
]
