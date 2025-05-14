from accounts.models import Employee
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


class FeedbackRequest(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_COMPLETED = 'completed'

    STATUS_CHOICES = [
        (STATUS_PENDING, _('Ожидает отзыва')),
        (STATUS_COMPLETED, _('Завершен')),
    ]

    goal = models.ForeignKey(
        Goal,
        on_delete=models.CASCADE,
        related_name='feedback_requests',
        verbose_name=_('Цель')
    )
    reviewer = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='feedback_requests_to_review',
        verbose_name=_('Рецензент')
    )
    requested_by = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='feedback_requests_created',
        verbose_name=_('Запрошено пользователем')
    )
    message = models.TextField(
        _('Сообщение для рецензента'),
        blank=True
    )
    status = models.CharField(
        _('Статус'),
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )
    created_dttm = models.DateTimeField(
        _('Дата создания'),
        auto_now_add=True
    )

    class Meta:
        verbose_name = _('Запрос отзыва')
        verbose_name_plural = _('Запросы отзывов')
        unique_together = ('goal', 'reviewer')
        db_table = 'feedback_requests'

    def __str__(self):
        return f"Запрос отзыва от {self.requested_by.user.get_full_name()} для {self.reviewer.user.get_full_name()}"


class PeerFeedback(models.Model):
    feedback_request = models.OneToOneField(
        FeedbackRequest,
        on_delete=models.CASCADE,
        related_name='feedback',
        verbose_name=_('Запрос отзыва')
    )
    rating = models.PositiveSmallIntegerField(
        _('Оценка'),
        choices=[(i, i) for i in range(1, 11)]
    )
    comments = models.TextField(
        _('Комментарии и впечатления')
    )
    areas_to_improve = models.TextField(
        _('Зоны для роста')
    )
    created_dttm = models.DateTimeField(
        _('Дата создания'),
        auto_now_add=True
    )

    class Meta:
        verbose_name = _('Отзыв коллеги')
        verbose_name_plural = _('Отзывы коллег')
        db_table = 'peer_feedback'

    def __str__(self):
        return f"Отзыв от {self.feedback_request.reviewer.user.get_full_name()} на цель {self.feedback_request.goal.title}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # При сохранении отзыва меняем статус запроса на "Завершен"
        if self.feedback_request.status != FeedbackRequest.STATUS_COMPLETED:
            self.feedback_request.status = FeedbackRequest.STATUS_COMPLETED
            self.feedback_request.save(update_fields=['status'])


class ExpertEvaluation(models.Model):
    goal = models.OneToOneField(
        Goal,
        on_delete=models.CASCADE,
        related_name='expert_evaluation',
        verbose_name=_('Цель')
    )
    expert = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='expert_evaluations',
        verbose_name=_('Лидер профессии')
    )
    final_rating = models.PositiveSmallIntegerField(
        _('Итоговая оценка'),
        choices=[(i, i) for i in range(1, 11)]
    )
    comments = models.TextField(
        _('Комментарии и впечатления')
    )
    areas_to_improve = models.TextField(
        _('Зоны для роста')
    )
    created_dttm = models.DateTimeField(
        _('Дата создания'),
        auto_now_add=True
    )

    class Meta:
        verbose_name = _('Итоговая оценка от лидера профессии')
        verbose_name_plural = _('Итоговые оценки от лидеров профессии')
        db_table = 'expert_evaluations'

    def __str__(self):
        return f"Оценка от {self.expert.user.get_full_name()} на цель {self.goal.title}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # При сохранении оценки лидера профессии меняем статус цели на "Завершена"
        if self.goal.status != Goal.STATUS_COMPLETED:
            self.goal.status = Goal.STATUS_COMPLETED
            self.goal.save(update_fields=['status'])
