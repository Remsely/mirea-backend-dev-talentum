from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import SelfAssessment


@admin.register(SelfAssessment)
class SelfAssessmentAdmin(admin.ModelAdmin):
    list_display = ('goal', 'rating', 'created_dttm')
    list_filter = ('rating', 'created_dttm')
    search_fields = ('goal__title', 'comments', 'areas_to_improve')
    raw_id_fields = ('goal',)
