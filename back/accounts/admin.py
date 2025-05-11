from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import User, Employee


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'username', 'email', 'first_name', 'last_name', 'role', 'is_staff'
    )
    list_filter = ('role', 'is_staff', 'is_active')
    readonly_fields = ('last_login', 'date_joined', 'registration_dttm')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    fieldsets = (
        (
            None,
            {
                'fields':
                    (
                        'username',
                        'password'
                    )
            }
        ),
        (
            _('Персональная информация'),
            {
                'fields': (
                    'first_name',
                    'last_name',
                    'email'
                )
            }
        ),
        (
            _('Права доступа'), {
            'fields': (
                'role',
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions'
            )
        }
        ),
        (
            _('Важные даты'),
            {
                'fields': (
                    'last_login',
                    'date_joined',
                    'registration_dttm'
                )
            }
        ),
    )


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'position', 'manager', 'hire_dt')
    list_filter = ('position',)
    search_fields = (
        'user__username',
        'user__first_name',
        'user__last_name',
        'user__email',
        'position'
    )
    raw_id_fields = ('user', 'manager')

    def full_name(self, obj):
        return obj.user.get_full_name()

    full_name.short_description = _('Полное имя')
