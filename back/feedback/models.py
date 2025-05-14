from django.db import models
from django.utils.translation import gettext_lazy as _

from goals.models import Goal


class SelfAssessment(models.Model):
    goal = models.OneToOneField(
        Goal,
        on_delete=models.CASCADE,
        related_name='self_assessment',
        verbose_name=_('Цель')
    )
    rating = models.PositiveSmallIntegerField(
        _('Оценка'),
        choices=[(i, i) for i in range(1, 11)]
    )
    comments = models.TextField(
        _('Комментарии')
    )
    areas_to_improve = models.TextField(
        _('Области для улучшения')
    )
    created_dttm = models.DateTimeField(
        _('Дата создания'),
        auto_now_add=True
    )

    class Meta:
        verbose_name = _('Самооценка')
        verbose_name_plural = _('Самооценки')
        db_table = 'goals_self_assessments'

    def __str__(self):
        return f"Самооценка для {self.goal.title}"
