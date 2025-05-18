from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from storages.backends.s3boto3 import S3Boto3Storage
from urllib.parse import urljoin


class ProfilePhotoStorage(S3Boto3Storage):
    """
    Кастомный класс хранилища для профильных фотографий.
    Хранит файлы в директории 'profile_photos'.
    """
    location = 'profile_photos'
    file_overwrite = False
    secure_urls = False
    
    def url(self, name):
        """
        Переопределяем метод url для явного формирования HTTP URLs
        """
        url = super().url(name)
        if url.startswith('https://'):
            return url.replace('https://', 'http://', 1)
        return url


class User(AbstractUser):
    ROLE_EMPLOYEE = 'employee'
    ROLE_EXPERTISE_LEADER = 'expertise_leader'
    ROLE_ADMIN = 'admin'

    ROLE_CHOICES = [
        (ROLE_EMPLOYEE, _('Сотрудник')),
        (ROLE_EXPERTISE_LEADER, _('Лидер профессии')),
        (ROLE_ADMIN, _('Администратор')),
    ]

    email = models.EmailField(
        _('email адрес'),
        unique=True
    )
    role = models.CharField(
        _('роль'),
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_EMPLOYEE
    )
    registration_dttm = models.DateTimeField(
        _('дата регистрации'),
        auto_now_add=True
    )
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']

    class Meta:
        verbose_name = _('пользователь')
        verbose_name_plural = _('пользователи')
        db_table = 'users'

    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"

    def is_manager(self):
        try:
            return self.employee_profile.subordinates.exists()
        except:
            return False


class Employee(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE,
        related_name='employee_profile'
    )
    hire_dt = models.DateField(
        _('дата приема на работу')
    )
    position = models.CharField(
        _('должность'),
        max_length=100
    )
    manager = models.ForeignKey(
        'self', null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='subordinates',
        verbose_name=_('руководитель')
    )
    profile_photo = models.ImageField(
        _('фото профиля'),
        upload_to='',  # Пустая строка, так как путь указан в storage
        storage=ProfilePhotoStorage(),
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = _('сотрудник')
        verbose_name_plural = _('сотрудники')
        db_table = 'employees'

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.position})"

    @property
    def full_name(self):
        return self.user.get_full_name()

    @property
    def email(self):
        return self.user.email

    @property
    def role(self):
        return self.user.role
