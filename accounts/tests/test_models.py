from django.test import TestCase
from django.utils import timezone

from accounts.models import User


class UserModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'johndoe',
            email='john@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )

    def test_str_returns_id_and_username(self):
        self.assertIn(str(self.user.pk), str(self.user))
        self.assertIn(self.user.username, str(self.user))

    def test_get_full_name(self):
        self.assertEqual(self.user.get_full_name(), 'John Doe')

    def test_is_blocked_false_by_default(self):
        self.assertFalse(self.user.is_blocked())

    def test_is_blocked_true_when_blocked_until_future(self):
        self.user.blocked_until = timezone.now() + timezone.timedelta(days=1)
        self.user.save()
        self.assertTrue(self.user.is_blocked())

    def test_is_blocked_true_when_inactive(self):
        self.user.is_active = False
        self.user.save()
        self.assertTrue(self.user.is_blocked())

    def test_get_average_rating_default(self):
        self.assertEqual(self.user.get_average_rating(), 0)
