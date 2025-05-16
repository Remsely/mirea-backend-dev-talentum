from django.test import SimpleTestCase, TestCase
from django.core.files.uploadedfile import SimpleUploadedFile

from accounts.models import User, Employee
from accounts.serializers import EmployeeSerializer, EmployeeDetailSerializer


class AuthSerializerTests(SimpleTestCase):
    """Тесты сериализаторов аутентификации без использования БД"""

    def test_custom_token_serializer_fields(self):
        """Тест структуры сериализатора токенов"""
        from accounts.serializers import CustomTokenObtainPairSerializer

        serializer = CustomTokenObtainPairSerializer()
        expected_fields = {'username', 'password'}
        self.assertTrue(expected_fields.issubset(serializer.fields.keys()))


class EmployeeSerializerTests(TestCase):
    """Тесты сериализаторов сотрудников с использованием БД"""
    
    def setUp(self):
        """Подготовка данных для тестов"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            first_name='Test',
            last_name='User',
            role='employee'
        )
        
        # Создаем тестовое изображение
        image_content = b'GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
        self.test_image = SimpleUploadedFile(
            'test_image.gif', 
            image_content, 
            content_type='image/gif'
        )
        
        self.employee = Employee.objects.create(
            user=self.user,
            hire_dt='2022-01-01',
            position='Test Position',
            profile_photo=self.test_image
        )
    
    def test_employee_serializer_fields(self):
        """Тест полей сериализатора сотрудника"""
        serializer = EmployeeSerializer(self.employee)
        
        # Проверяем наличие поля profile_photo_url
        self.assertIn('profile_photo_url', serializer.data)
        self.assertIsNotNone(serializer.data['profile_photo_url'])
        
        # Проверяем, что URL правильно формируется
        self.assertTrue(isinstance(serializer.data['profile_photo_url'], str))
        self.assertIn('test_image', serializer.data['profile_photo_url'])
    
    def test_employee_detail_serializer_fields(self):
        """Тест полей детального сериализатора сотрудника"""
        serializer = EmployeeDetailSerializer(self.employee)
        
        # Проверяем наличие поля profile_photo_url
        self.assertIn('profile_photo_url', serializer.data)
        self.assertIsNotNone(serializer.data['profile_photo_url'])
        
        # Проверяем, что profile_photo присутствует в fields
        self.assertIn('profile_photo', serializer.data)
