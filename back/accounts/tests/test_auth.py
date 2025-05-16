from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import User, Employee


class AuthenticationTests(TestCase):
    """Тесты аутентификации выделены в отдельный класс"""

    @classmethod
    def setUpTestData(cls):
        """Создаем данные один раз для всех тестов в классе"""
        cls.employee_user = User.objects.create_user(
            username='employee',
            email='employee@example.com',
            password='password123',
            first_name='Test',
            last_name='User',
            role='employee'
        )

        cls.manager_user = User.objects.create_user(
            username='manager',
            email='manager@example.com',
            password='password123',
            first_name='Manager',
            last_name='User',
            role='employee'
        )

        # Создаем профиль сотрудника для employee_user
        cls.employee = Employee.objects.create(
            user=cls.employee_user,
            hire_dt='2021-01-01',
            position='Developer',
            profile_photo=None
        )

        # Создаем профиль менеджера с подчиненными
        cls.manager = Employee.objects.create(
            user=cls.manager_user,
            hire_dt='2020-01-01',
            position='Team Lead',
            profile_photo=None
        )

        # Устанавливаем связь менеджер-подчиненный
        cls.employee.manager = cls.manager
        cls.employee.save()

        # Пользователь без профиля сотрудника
        cls.user_without_profile = User.objects.create_user(
            username='noemployee',
            email='noemployee@example.com',
            password='password123',
            first_name='No',
            last_name='Profile',
            role='employee'
        )

    def setUp(self):
        """Создаем клиент для каждого теста"""
        self.client = APIClient()

    def test_user_login_success(self):
        """Тест успешной аутентификации пользователя и получения токена"""
        url = reverse('token_obtain_pair')
        data = {
            'username': 'employee',
            'password': 'password123'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['username'], 'employee')
        self.assertEqual(response.data['email'], 'employee@example.com')
        self.assertTrue(response.data['has_employee_profile'])
        self.assertFalse(response.data['is_manager'])

    def test_user_login_manager(self):
        """Тест авторизации менеджера с проверкой is_manager"""
        url = reverse('token_obtain_pair')
        data = {
            'username': 'manager',
            'password': 'password123'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_manager'])
        self.assertEqual(response.data['role'],
                         'employee')  # Роль employee, но статус manager

    def test_user_login_without_profile(self):
        """Тест авторизации пользователя без профиля сотрудника"""
        url = reverse('token_obtain_pair')
        data = {
            'username': 'noemployee',
            'password': 'password123'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['has_employee_profile'])

    def test_user_login_invalid_credentials(self):
        """Тест авторизации с неверными учетными данными"""
        url = reverse('token_obtain_pair')
        data = {
            'username': 'employee',
            'password': 'wrongpassword'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh(self):
        """Тест обновления токена"""

        url = reverse('token_obtain_pair')
        data = {
            'username': 'employee',
            'password': 'password123'
        }
        response = self.client.post(url, data, format='json')
        refresh_token = response.data['refresh']

        url = reverse('token_refresh')
        data = {'refresh': refresh_token}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
