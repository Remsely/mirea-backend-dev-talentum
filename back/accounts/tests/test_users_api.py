from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import User


class UserAPITests(TestCase):
    """Тесты API пользователей"""

    @classmethod
    def setUpTestData(cls):
        """Создаем базовые данные для всех тестов класса"""
        # Создаем администратора
        cls.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='password123',
            first_name='Admin',
            last_name='User',
            role='admin'
        )

        # Создаем обычного сотрудника
        cls.employee_user = User.objects.create_user(
            username='employee',
            email='employee@example.com',
            password='password123',
            first_name='Test',
            last_name='User',
            role='employee'
        )

        # Создаем еще одного сотрудника для тестов
        cls.employee2_user = User.objects.create_user(
            username='employee2',
            email='employee2@example.com',
            password='password123',
            first_name='Second',
            last_name='Employee',
            role='employee'
        )

        # Создаем менеджера для тестов
        cls.manager_user = User.objects.create_user(
            username='manager',
            email='manager@example.com',
            password='password123',
            first_name='Manager',
            last_name='User',
            role='employee'
        )

        # Пользователь без профиля сотрудника
        cls.user_without_profile = User.objects.create_user(
            username='noemployee',
            email='noemployee@example.com',
            password='password123',
            first_name='No',
            last_name='Profile',
            role='employee'
        )

        # Запоминаем начальное количество пользователей
        cls.initial_user_count = User.objects.count()

    def setUp(self):
        """Подготовка для каждого теста"""
        self.client = APIClient()

    def test_user_list_admin_allowed(self):
        """Тест доступа администратора к списку пользователей"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('user-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), self.initial_user_count)

    def test_user_list_employee_forbidden(self):
        """Тест запрета доступа обычного пользователя к списку пользователей"""
        self.client.force_authenticate(user=self.employee_user)
        url = reverse('user-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_create_admin_allowed(self):
        """Тест создания пользователя администратором"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('user-list')
        data = {
            'username': 'newuser',
            'password': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'employee'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['username'], 'newuser')
        self.assertIn('id', response.data)  # Проверяем, что ID включен в ответ
        self.assertEqual(response.data['role'], 'employee')

        # Проверяем, что пользователь действительно создан в БД
        self.assertTrue(User.objects.filter(username='newuser').exists())

        # Проверяем, что счетчик увеличился на 1
        self.assertEqual(User.objects.count(), self.initial_user_count + 1)

    def test_user_create_password_mismatch(self):
        """Тест валидации несовпадающих паролей при создании пользователя"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('user-list')
        data = {
            'username': 'newuser',
            'password': 'password123',
            'password2': 'differentpassword',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'employee'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_user_create_employee_forbidden(self):
        """Тест запрета создания пользователя обычным сотрудником"""
        self.client.force_authenticate(user=self.employee_user)
        url = reverse('user-list')
        data = {
            'username': 'newuser',
            'password': 'password123',
            'password2': 'password123',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'employee'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_retrieve_admin_any_user(self):
        """Тест получения информации о любом пользователе администратором"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('user-detail', kwargs={'pk': self.employee_user.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'employee')

    def test_user_retrieve_self(self):
        """Тест получения пользователем информации о себе"""
        self.client.force_authenticate(user=self.employee_user)
        url = reverse('user-detail', kwargs={'pk': self.employee_user.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'employee')

    def test_user_retrieve_other_forbidden(self):
        """Тест запрета получения пользователем информации о другом пользователе"""
        self.client.force_authenticate(user=self.employee_user)
        url = reverse('user-detail', kwargs={'pk': self.manager_user.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_update_admin_allowed(self):
        """Тест обновления информации о пользователе администратором"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('user-detail', kwargs={'pk': self.employee_user.id})
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'updated@example.com'
        }
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Updated')
        self.assertEqual(response.data['last_name'], 'Name')
        self.assertEqual(response.data['email'], 'updated@example.com')

    def test_user_update_self_allowed(self):
        """Тест обновления пользователем своих данных"""
        self.client.force_authenticate(user=self.employee_user)
        url = reverse('user-detail', kwargs={'pk': self.employee_user.id})
        data = {
            'first_name': 'NewFirstName',
            'last_name': 'NewLastName'
        }
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'NewFirstName')
        self.assertEqual(response.data['last_name'], 'NewLastName')

    def test_user_update_other_forbidden(self):
        """Тест запрета обновления пользователем данных другого пользователя"""
        self.client.force_authenticate(user=self.employee_user)
        url = reverse('user-detail', kwargs={'pk': self.manager_user.id})
        data = {
            'first_name': 'Attempt',
            'last_name': 'Change'
        }
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_delete_admin_allowed(self):
        """Тест удаления пользователя администратором"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('user-detail',
                      kwargs={'pk': self.user_without_profile.id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            User.objects.filter(id=self.user_without_profile.id).exists())

    def test_user_delete_self_forbidden(self):
        """Тест запрета удаления пользователем своего аккаунта"""
        self.client.force_authenticate(user=self.employee_user)
        url = reverse('user-detail', kwargs={'pk': self.employee_user.id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(User.objects.filter(id=self.employee_user.id).exists())

    def test_user_search_admin_allowed(self):
        """Тест поиска пользователей администратором"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('user-search')
        response = self.client.get(f"{url}?q=emp")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Ищем пользователей с "emp" в имени/username/email
        employee_count = User.objects.filter(
            username__icontains='emp'
        ).count()
        self.assertEqual(len(response.data), employee_count)

    def test_user_search_admin_empty_query(self):
        """Тест поиска с пустым запросом"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('user-search')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data),
                         0)  # пустой ответ при пустом запросе

    def test_user_search_employee_forbidden(self):
        """Тест запрета поиска пользователей обычным сотрудником"""
        self.client.force_authenticate(user=self.employee_user)
        url = reverse('user-search')
        response = self.client.get(f"{url}?q=emp")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_me(self):
        """Тест получения информации о текущем пользователе"""
        self.client.force_authenticate(user=self.employee_user)
        url = reverse('user-me')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'employee')
        self.assertEqual(response.data['email'], 'employee@example.com')
