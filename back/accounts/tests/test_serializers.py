from django.test import SimpleTestCase


class AuthSerializerTests(SimpleTestCase):
    """Тесты сериализаторов аутентификации без использования БД"""

    def test_custom_token_serializer_fields(self):
        """Тест структуры сериализатора токенов"""
        from accounts.serializers import CustomTokenObtainPairSerializer

        serializer = CustomTokenObtainPairSerializer()
        expected_fields = {'username', 'password'}
        self.assertTrue(expected_fields.issubset(serializer.fields.keys()))
