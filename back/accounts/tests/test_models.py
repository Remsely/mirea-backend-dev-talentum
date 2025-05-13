from django.test import SimpleTestCase, TestCase

from accounts.models import User, Employee


class UserModelSimpleTests(SimpleTestCase):
    """Быстрые тесты логики модели User, не требующие базы данных"""

    def test_user_string_representation(self):
        user = User(username='testuser', first_name='Test', last_name='User')
        self.assertEqual(str(user), "Test User (testuser)")


class UserModelMethodTests(TestCase):
    """Тесты методов модели User"""

    def test_is_manager_method(self):
        """Тест метода is_manager модели User"""
        # Создаем менеджера и его подчиненного
        manager_user = User.objects.create_user(
            username='method_manager',
            email='method_manager@example.com',
            password='password123',
            first_name='Method',
            last_name='Manager',
            role='employee'
        )

        manager = Employee.objects.create(
            user=manager_user,
            hire_dt='2020-01-01',
            position='Method Manager'
        )

        employee_user = User.objects.create_user(
            username='method_employee',
            email='method_employee@example.com',
            password='password123',
            first_name='Method',
            last_name='Employee',
            role='employee'
        )

        employee = Employee.objects.create(
            user=employee_user,
            hire_dt='2021-01-01',
            position='Method Employee',
            manager=manager
        )

        # Проверяем, что manager_user определяется как менеджер
        self.assertTrue(manager_user.is_manager())

        # Проверяем, что employee_user не определяется как менеджер
        self.assertFalse(employee_user.is_manager())

        # Создаем пользователя без профиля и проверяем, что он не менеджер
        no_profile_user = User.objects.create_user(
            username='no_profile',
            email='no_profile@example.com',
            password='password123',
            first_name='No',
            last_name='Profile',
            role='employee'
        )

        self.assertFalse(no_profile_user.is_manager())
