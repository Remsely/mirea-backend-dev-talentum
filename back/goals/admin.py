from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Goal, Progress


class ProgressInline(admin.TabularInline):
    model = Progress
    extra = 0


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'employee_name',
        'status',
        'start_period',
        'end_period',
        'created_dttm'
    )
    list_filter = ('status', 'start_period', 'end_period')
    search_fields = (
        'title',
        'description',
        'employee__user__first_name',
        'employee__user__last_name'
    )
    date_hierarchy = 'created_dttm'
    raw_id_fields = ('employee',)
    inlines = [ProgressInline]

    def employee_name(self, obj):
        return obj.employee.user.get_full_name()

    employee_name.short_description = _('Сотрудник')


@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    list_display = ('goal', 'created_dttm')
    list_filter = ('created_dttm',)
    search_fields = ('goal__title', 'description')
    date_hierarchy = 'created_dttm'
    raw_id_fields = ('goal',)
