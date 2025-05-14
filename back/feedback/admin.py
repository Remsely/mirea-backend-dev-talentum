from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import SelfAssessment, FeedbackRequest, PeerFeedback, ExpertEvaluation


@admin.register(SelfAssessment)
class SelfAssessmentAdmin(admin.ModelAdmin):
    list_display = ('goal', 'rating', 'created_dttm')
    list_filter = ('rating', 'created_dttm')
    search_fields = ('goal__title', 'comments', 'areas_to_improve')
    raw_id_fields = ('goal',)


@admin.register(FeedbackRequest)
class FeedbackRequestAdmin(admin.ModelAdmin):
    list_display = ('goal', 'reviewer', 'requested_by', 'status', 'created_dttm')
    list_filter = ('status', 'created_dttm')
    search_fields = (
        'goal__title', 
        'reviewer__user__first_name', 
        'reviewer__user__last_name',
        'requested_by__user__first_name', 
        'requested_by__user__last_name', 
        'message'
        )
    raw_id_fields = ('goal', 'reviewer', 'requested_by')


@admin.register(PeerFeedback)
class PeerFeedbackAdmin(admin.ModelAdmin):
    list_display = ('get_goal', 'get_reviewer', 'rating', 'created_dttm')
    list_filter = ('rating', 'created_dttm')
    search_fields = (
        'feedback_request__goal__title', 
        'feedback_request__reviewer__user__first_name',
        'feedback_request__reviewer__user__last_name', 
        'comments', 
        'areas_to_improve'
        )
    raw_id_fields = ('feedback_request',)
    
    def get_goal(self, obj):
        return obj.feedback_request.goal
    get_goal.short_description = _('Цель')
    get_goal.admin_order_field = 'feedback_request__goal'
    
    def get_reviewer(self, obj):
        return obj.feedback_request.reviewer.user.get_full_name()
    get_reviewer.short_description = _('Рецензент')
    get_reviewer.admin_order_field = 'feedback_request__reviewer'


@admin.register(ExpertEvaluation)
class ExpertEvaluationAdmin(admin.ModelAdmin):
    list_display = ('goal', 'expert', 'final_rating', 'created_dttm')
    list_filter = ('final_rating', 'created_dttm')
    search_fields = (
        'goal__title', 
        'expert__user__first_name', 
        'expert__user__last_name',
        'comments', 
        'areas_to_improve'
        )
    raw_id_fields = ('goal', 'expert')
