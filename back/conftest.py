import os
import pytest
import tempfile
from django.conf import settings
from django.test.utils import override_settings


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
        storage_settings = {
            'DEFAULT_FILE_STORAGE': 'django.core.files.storage.FileSystemStorage',
            'MEDIA_ROOT': temp_dir,
        }
        with override_settings(**storage_settings):
            yield temp_dir 