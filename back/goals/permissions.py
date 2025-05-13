from rest_framework import permissions

from goals.models import Goal


class IsEmployeeOwnerOrManagerOrExpertiseLeaderOrAdmin(
    permissions.BasePermission
):
    """
    Разрешение для проверки, является ли пользователь владельцем цели,
    руководителем владельца или администратором.
    Для лидеров профессии добавлен доступ только на чтение для целей в статусе "Ожидает оценки"
    """

    def has_permission(self, request, view):
        if request.user.role == 'admin':
            return True

        try:
            if hasattr(view, 'kwargs') and 'goal_pk' in view.kwargs:
                goal_pk = view.kwargs['goal_pk']
                goal = Goal.objects.get(pk=goal_pk)

                if (request.user.role == 'expertise_leader'
                        and request.method in permissions.SAFE_METHODS):
                    if goal.status == Goal.STATUS_PENDING_ASSESSMENT:
                        return True

                employee = request.user.employee_profile

                if goal.employee == employee:
                    return True
                if goal.employee.manager == employee:
                    return True

                return False

            return True
        except Exception:
            return False

    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True

        if (request.user.role == 'expertise_leader'
                and request.method in permissions.SAFE_METHODS):
            goal = None
            if hasattr(obj, 'goal'):
                goal = obj.goal
            elif hasattr(obj, 'employee'):
                goal = obj

            if goal and goal.status == Goal.STATUS_PENDING_ASSESSMENT:
                return True

        try:
            employee = request.user.employee_profile

            if hasattr(obj, 'employee'):
                if obj.employee == employee:
                    return True
                if obj.employee.manager == employee:
                    return True

            if hasattr(obj, 'goal'):
                if obj.goal.employee == employee:
                    return True
                if obj.goal.employee.manager == employee:
                    return True

            return False
        except Exception:
            return False


class IsManager(permissions.BasePermission):
    """
    Разрешение для проверки, является ли пользователь руководителем.
    """

    def has_permission(self, request, view):
        try:
            return (request.user.role == 'manager' or (
                    hasattr(request.user, 'employee_profile')
                    and request.user.employee_profile.subordinates.exists()))
        except Exception:
            return False

    def has_object_permission(self, request, view, obj):
        try:
            employee = request.user.employee_profile

            if hasattr(obj, 'employee'):
                return obj.employee.manager == employee
            if hasattr(obj, 'goal'):
                return obj.goal.employee.manager == employee
            return False
        except Exception:
            return False


class IsExpertiseLeader(permissions.BasePermission):
    """
    Разрешение для проверки, является ли пользователь лидером профессии.
    """

    def has_permission(self, request, view):
        return request.user.role == 'expertise_leader'


def _has_access_to_goal(user, goal):
    if user.role == 'admin':
        return True

    try:
        employee = user.employee_profile

        if goal.employee == employee:
            return True
        if goal.employee.manager == employee:
            return True
        if (user.role == 'expertise_leader'
                and goal.status == 'pending_assessment'):
            return True

        return False
    except:
        return False


def _can_edit_goal(user, goal):
    try:
        return (goal.status == 'draft'
                and goal.employee.user == user)
    except:
        return False


class CanManageGoal(permissions.BasePermission):
    """
    Разрешение для управления целями с учетом статуса цели.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return _has_access_to_goal(request.user, obj)

        if view.action in ['update', 'partial_update', 'destroy']:
            if obj.status != Goal.STATUS_DRAFT:
                from rest_framework.exceptions import ValidationError
                raise ValidationError(
                    "Обновлять/удалять можно только цели в статусе черновика."
                )
            return _can_edit_goal(request.user, obj)

        if view.action == 'submit':
            if not obj.can_be_submitted():
                from rest_framework.exceptions import ValidationError
                raise ValidationError(
                    "Цель не может быть отправлена на согласование"
                )
            return obj.employee.user == request.user

        if view.action == 'approve':
            try:
                if not obj.can_be_approved():
                    from rest_framework.exceptions import ValidationError
                    raise ValidationError(
                        "Цель не может быть согласована"
                    )
                return obj.employee.manager.user == request.user
            except Exception:
                return False

        if view.action == 'complete':
            if not obj.can_complete():
                from rest_framework.exceptions import ValidationError
                raise ValidationError(
                    "Цель не может быть завершена"
                )
            return obj.employee.user == request.user

        return False
