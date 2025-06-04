from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from ..permissions import IsSuperUser, IsMentor


class DummyView(APIView):
    permission_classes = []  # Будем менять в тестах


class UserMock:
    def __init__(self, is_authenticated=True, is_mentor=False, is_superuser=False):
        self.is_authenticated = is_authenticated
        self.is_mentor = is_mentor
        self.is_superuser = is_superuser


class PermissionsTestCase(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def test_is_mentor_permission(self):
        # Неаутентифицированный
        user = UserMock(is_authenticated=False, is_mentor=True)
        request = self.factory.get('/')
        request.user = user
        perm = IsMentor()
        self.assertFalse(perm.has_permission(request, DummyView()))

        # Аутентифицированный, не ментор
        user = UserMock(is_authenticated=True, is_mentor=False)
        request.user = user
        self.assertFalse(perm.has_permission(request, DummyView()))

        # Аутентифицированный, ментор
        user = UserMock(is_authenticated=True, is_mentor=True)
        request.user = user
        self.assertTrue(perm.has_permission(request, DummyView()))

    def test_is_superuser_permission(self):
        perm = IsSuperUser()

        # Неаутентифицированный
        user = UserMock(is_authenticated=False, is_superuser=True)
        request = self.factory.get('/')
        request.user = user
        self.assertFalse(perm.has_permission(request, DummyView()))

        # Аутентифицированный, не суперюзер
        user = UserMock(is_authenticated=True, is_superuser=False)
        request.user = user
        self.assertFalse(perm.has_permission(request, DummyView()))

        # Аутентифицированный, суперюзер
        user = UserMock(is_authenticated=True, is_superuser=True)
        request.user = user
        self.assertTrue(perm.has_permission(request, DummyView()))
