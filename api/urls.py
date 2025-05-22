from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . views import UserViewSet, SlotViewSet, ReviewViewSet


router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'slots', SlotViewSet)
router.register(r'reviews', ReviewViewSet)

urlpatterns = [
    path('', include(router.urls))
]
