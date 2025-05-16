from django.test import SimpleTestCase, TestCase
from django.core.files.uploadedfile import SimpleUploadedFile

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


class EmployeeModelTests(TestCase):
    """Тесты модели Employee"""

    def test_employee_profile_photo(self):
        """Тест поля profile_photo модели Employee"""
        user = User.objects.create_user(
            username='test_photo',
            email='test_photo@example.com',
            password='password123',
            first_name='Test',
            last_name='Photo',
            role='employee'
        )

        # Создаем тестовое изображение
        image_content = b'GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
        test_image = SimpleUploadedFile(
            'test_image.gif', 
            image_content, 
            content_type='image/gif'
        )

        # Создаем сотрудника с фото профиля
        employee = Employee.objects.create(
            user=user,
            hire_dt='2022-01-01',
            position='Test Position',
            profile_photo=test_image
        )

        # Проверяем, что фото сохранилось
        self.assertTrue(employee.profile_photo)
        self.assertIn('test_image', employee.profile_photo.name)
