from django_filters.rest_framework import FilterSet, \
    BaseInFilter, CharFilter

from goals.models import Goal


class CharInFilter(BaseInFilter, CharFilter):
    pass


class GoalFilterSet(FilterSet):
    status = CharInFilter(field_name='status', lookup_expr='in')

    class Meta:
        model = Goal
        fields = ['status', 'employee', 'start_period', 'end_period']
