from rest_framework import permissions

from goals.models import Goal


class CanRequestFeedback(permissions.BasePermission):
    """
    Разрешение для запроса отзывов.
    Пользователь может запрашивать отзывы только для своих целей,
    и только если цель в статусе "Ожидает оценки".
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        try:
            request.user.employee_profile
            return True
        except:
            return False

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Goal):
            is_owner = obj.employee == request.user.employee_profile
            is_pending_assessment = obj.status == Goal.STATUS_PENDING_ASSESSMENT
            return is_owner and is_pending_assessment
        return False


class CanProvideFeedback(permissions.BasePermission):
    """
    Разрешение для предоставления отзыва.
    Пользователь может предоставить отзыв, только если он является рецензентом
    в запросе отзыва и запрос в статусе "Ожидает отзыва".
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        try:
            request.user.employee_profile
            return True
        except:
            return False

    def has_object_permission(self, request, view, obj):
        return (obj.reviewer == request.user.employee_profile and
                obj.status == 'pending')


class CanProvideExpertEvaluation(permissions.BasePermission):
    """
    Разрешение для предоставления экспертной оценки.
    Пользователь может предоставить экспертную оценку, только если он
    является лидером профессии и цель в статусе "Ожидает оценки".
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        return request.user.role == 'expertise_leader'

    def has_object_permission(self, request, view, obj):
        return obj.status == Goal.STATUS_PENDING_ASSESSMENT
