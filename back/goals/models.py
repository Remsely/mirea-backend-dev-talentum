from django.db import models
from django.utils.translation import gettext_lazy as _

from accounts.models import Employee


class Goal(models.Model):
    STATUS_DRAFT = 'draft'
    STATUS_PENDING_APPROVAL = 'pending_approval'
    STATUS_APPROVED = 'approved'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_PENDING_ASSESSMENT = 'pending_assessment'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_DRAFT, _('Черновик')),
        (STATUS_PENDING_APPROVAL, _('На согласовании')),
        (STATUS_APPROVED, _('Согласовано')),
        (STATUS_IN_PROGRESS, _('В процессе')),
        (STATUS_PENDING_ASSESSMENT, _('Ожидает оценки')),
        (STATUS_COMPLETED, _('Завершено')),
        (STATUS_CANCELLED, _('Отменено')),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='goals',
        verbose_name=_('Сотрудник')
    )
    title = models.CharField(
        _('Название'),
        max_length=255
    )
    description = models.TextField(
        _('Описание')
    )
    expected_results = models.TextField(
        _('Ожидаемые результаты')
    )
    start_period = models.DateField(
        _('Начало периода')
    )
    end_period = models.DateField(
        _('Конец периода')
    )
    status = models.CharField(
        _('Статус'),
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT
    )
    created_dttm = models.DateTimeField(
        _('Дата создания'),
        auto_now_add=True
    )
    updated_dttm = models.DateTimeField(
        _('Дата обновления'),
        auto_now=True
    )

    class Meta:
        verbose_name = _('Цель')
        verbose_name_plural = _('Цели')
        ordering = ['-created_dttm']
        db_table = 'goals'

    def __str__(self):
        return f"{self.title} - {self.employee.user.get_full_name()}"

    def can_be_submitted(self):
        return self.status == self.STATUS_DRAFT

    def can_be_approved(self):
        return self.status == self.STATUS_PENDING_APPROVAL

    def can_add_progress(self):
        return self.status == self.STATUS_IN_PROGRESS

    def can_add_self_assessment(self):
        return (self.status == self.STATUS_IN_PROGRESS
                or self.status == self.STATUS_PENDING_ASSESSMENT)

    def can_complete(self):
        return self.status == self.STATUS_IN_PROGRESS


class Progress(models.Model):
    goal = models.ForeignKey(
        Goal,
        on_delete=models.CASCADE,
        related_name='progress_entries',
        verbose_name=_('Цель')
    )
    description = models.TextField(
        _('Описание прогресса')
    )
    created_dttm = models.DateTimeField(
        _('Дата создания'),
        auto_now_add=True
    )

    class Meta:
        verbose_name = _('Запись о прогрессе')
        verbose_name_plural = _('Записи о прогрессе')
        ordering = ['-created_dttm']
        db_table = 'goals_progresses'

    def __str__(self):
        return (f"Прогресс для {self.goal.title} "
                f"от {self.created_dttm.strftime('%d.%m.%Y')}")
