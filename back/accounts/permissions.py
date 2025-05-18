from rest_framework import permissions


class IsAdminOrSelf(permissions.BasePermission):
    """
    Разрешение, позволяющее пользователю редактировать только свой профиль
    или администраторам редактировать любой профиль.
    """

    def has_object_permission(self, request, view, obj):
        if obj.id == request.user.id:
            return True
        return request.user.is_staff or request.user.role == 'admin'


class IsAdminOnly(permissions.BasePermission):
    """
    Разрешение, позволяющее только администраторам выполнять действие.
    """

    def has_permission(self, request, view):
        return True # TODO: remove this

class IsEmployeeOwnerOrAdmin(permissions.BasePermission):
    """
    Разрешение, позволяющее редактировать профиль сотрудника, только:
    1. Самому сотруднику
    2. Администратору
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff or request.user.role == 'admin':
            return True

        if (hasattr(request.user, 'employee_profile')
                and obj.id == request.user.employee_profile.id):
            return True

        return False
