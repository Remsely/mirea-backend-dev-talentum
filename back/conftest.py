import os
import pytest
import tempfile
from django.conf import settings
from django.test.utils import override_settings
from django.core.files.storage import FileSystemStorage


class TemporaryDirectory:
    """Контекстный менеджер для временной директории"""
    def __init__(self):
        self.dir = tempfile.mkdtemp()

    def __enter__(self):
        return self.dir

    def __exit__(self, exc_type, exc_val, exc_tb):
        import shutil
        shutil.rmtree(self.dir)


@pytest.fixture(scope='function', autouse=True)
def use_temp_storage_for_tests():
    """
    Переопределяем хранилище на файловое в памяти для тестов
    """
    with TemporaryDirectory() as temp_dir:
        # Сохраняем настройки, чтобы потом вернуть их
        original_storage_settings = {}
        storage_settings = {
            'DEFAULT_FILE_STORAGE': 'django.core.files.storage.FileSystemStorage',
            'MEDIA_ROOT': temp_dir,
            # Отключаем настройки S3 
            'AWS_ACCESS_KEY_ID': None,
            'AWS_SECRET_ACCESS_KEY': None,
            'AWS_STORAGE_BUCKET_NAME': None,
            'AWS_S3_ENDPOINT_URL': None,
            'AWS_S3_CUSTOM_DOMAIN': None,
            'AWS_QUERYSTRING_AUTH': None,
            'AWS_S3_FILE_OVERWRITE': None,
            'AWS_DEFAULT_ACL': None,
            'AWS_S3_VERIFY': None,
            'AWS_S3_ADDRESSING_STYLE': None,
            'AWS_S3_SECURE_URLS': None,
        }

        # Патчим модель Employee, чтобы она использовала FileSystemStorage вместо ProfilePhotoStorage
        try:
            # Импортируем здесь, чтобы предотвратить циклические импорты
            from accounts.models import Employee
            
            # Сохраняем оригинальную field до патча
            original_field = Employee._meta.get_field('profile_photo')
            original_storage = original_field.storage
            
            # Заменяем storage на FileSystemStorage
            Employee._meta.get_field('profile_photo').storage = FileSystemStorage(location=temp_dir)
            
            with override_settings(**storage_settings):
                yield temp_dir
                
            # Восстанавливаем оригинальное хранилище после тестов
            Employee._meta.get_field('profile_photo').storage = original_storage
            
        except ImportError:
            # Если не получилось импортировать модель, просто переопределяем настройки
            with override_settings(**storage_settings):
                yield temp_dir 