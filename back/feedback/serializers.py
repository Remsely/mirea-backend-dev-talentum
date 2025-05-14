from rest_framework import serializers

from accounts.serializers import EmployeeSerializer
from .models import SelfAssessment, FeedbackRequest, PeerFeedback, ExpertEvaluation


class SelfAssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SelfAssessment
        fields = (
            'id',
            'rating',
            'comments',
            'areas_to_improve',
            'created_dttm'
        )
        read_only_fields = ('id', 'created_dttm')


class FeedbackRequestListSerializer(serializers.ModelSerializer):
    reviewer = EmployeeSerializer(read_only=True)
    requested_by = EmployeeSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = FeedbackRequest
        fields = (
            'id',
            'goal',
            'reviewer',
            'requested_by',
            'message',
            'status',
            'status_display',
            'created_dttm'
        )
        read_only_fields = ('id', 'goal', 'status', 'status_display', 'created_dttm')


class FeedbackRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedbackRequest
        fields = (
            'id',
            'reviewer',
            'message',
            'created_dttm'
        )
        read_only_fields = ('id', 'created_dttm')
    
    def validate_reviewer(self, value):
        request = self.context.get('request')
        if request and request.user.employee_profile == value:
            raise serializers.ValidationError("Вы не можете запросить отзыв у самого себя")
        return value

    def validate(self, attrs):
        goal_id = self.context.get('goal_id')
        if goal_id and FeedbackRequest.objects.filter(
            goal_id=goal_id,
            reviewer=attrs['reviewer']
        ).exists():
            raise serializers.ValidationError(
                {"reviewer": "Запрос отзыва от этого сотрудника уже существует"}
            )
        return attrs

    def create(self, validated_data):
        goal_id = self.context['goal_id']
        user = self.context['request'].user
        
        if 'goal_id' in validated_data:
            validated_data.pop('goal_id')
            
        feedback_request = FeedbackRequest.objects.create(
            goal_id=goal_id,
            requested_by=user.employee_profile,
            **validated_data
        )
        
        return feedback_request


class PeerFeedbackSerializer(serializers.ModelSerializer):
    reviewer = serializers.SerializerMethodField()
    goal = serializers.SerializerMethodField()
    
    class Meta:
        model = PeerFeedback
        fields = (
            'id',
            'reviewer',
            'goal',
            'rating',
            'comments',
            'areas_to_improve',
            'created_dttm'
        )
        read_only_fields = ('id', 'reviewer', 'goal', 'created_dttm')
    
    def get_reviewer(self, obj):
        return EmployeeSerializer(obj.feedback_request.reviewer).data
    
    def get_goal(self, obj):
        return {
            'id': obj.feedback_request.goal.id,
            'title': obj.feedback_request.goal.title
        }


class ExpertEvaluationSerializer(serializers.ModelSerializer):
    expert = EmployeeSerializer(read_only=True)
    
    class Meta:
        model = ExpertEvaluation
        fields = (
            'id',
            'expert',
            'final_rating',
            'comments',
            'areas_to_improve',
            'created_dttm'
        )
        read_only_fields = ('id', 'expert', 'created_dttm')
    
    def create(self, validated_data):
        goal_id = self.context['goal_id']
        user = self.context['request'].user
        
        if 'goal_id' in validated_data:
            validated_data.pop('goal_id')
        
        expert_evaluation = ExpertEvaluation.objects.create(
            goal_id=goal_id,
            expert=user.employee_profile,
            **validated_data
        )
        return expert_evaluation 
