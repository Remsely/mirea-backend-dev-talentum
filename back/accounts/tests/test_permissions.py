from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import User


class PermissionTests(TestCase):
    """Тесты проверки разрешений"""

    @classmethod
    def setUpTestData(cls):
        """Создаем данные для тестирования разрешений"""
        cls.admin_user = User.objects.create_superuser(
            username='admin_perm',
            email='admin_perm@example.com',
            password='password123',
            first_name='Admin',
            last_name='Permission',
            role='admin'
        )

        cls.regular_user = User.objects.create_user(
            username='user_perm',
            email='user_perm@example.com',
            password='password123',
            first_name='User',
            last_name='Permission',
            role='employee'
        )

        cls.user2 = User.objects.create_user(
            username='user2_perm',
            email='user2_perm@example.com',
            password='password123',
            first_name='User2',
            last_name='Permission',
            role='employee'
        )

    def setUp(self):
        self.client = APIClient()

    def test_admin_permission_checks(self):
        """Тест разрешений администратора"""
        self.client.force_authenticate(user=self.admin_user)

        # Администратор может получить список пользователей
        url = reverse('user-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Администратор может получить информацию о любом пользователе
        url = reverse('user-detail', kwargs={'pk': self.regular_user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Администратор может удалить пользователя
        url = reverse('user-detail', kwargs={'pk': self.user2.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_regular_user_permission_checks(self):
        """Тест разрешений обычного пользователя"""
        self.client.force_authenticate(user=self.regular_user)

        # Обычный пользователь не может получить список пользователей
        url = reverse('user-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Обычный пользователь может получить информацию о себе
        url = reverse('user-detail', kwargs={'pk': self.regular_user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Обычный пользователь не может получить информацию о другом пользователе
        url = reverse('user-detail', kwargs={'pk': self.user2.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
