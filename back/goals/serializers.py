from rest_framework import serializers

from accounts.serializers import EmployeeSerializer
from feedback.serializers import SelfAssessmentSerializer
from .models import Goal, Progress


class GoalListSerializer(serializers.ModelSerializer):
    employee = EmployeeSerializer(read_only=True)
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )

    class Meta:
        model = Goal
        fields = (
            'id',
            'title',
            'employee',
            'status',
            'status_display',
            'start_period',
            'end_period',
            'created_dttm',
            'updated_dttm'
        )
        read_only_fields = ('id', 'created_dttm', 'updated_dttm')


class ProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Progress
        fields = ('id', 'description', 'created_dttm')
        read_only_fields = ('id', 'created_dttm')


class GoalDetailSerializer(serializers.ModelSerializer):
    employee = EmployeeSerializer(read_only=True)
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    progress_updates = ProgressSerializer(
        source='progress_entries',
        many=True,
        read_only=True
    )
    self_assessment = SelfAssessmentSerializer(read_only=True)
    can_be_submitted = serializers.SerializerMethodField()
    can_be_approved = serializers.SerializerMethodField()
    can_add_progress = serializers.SerializerMethodField()
    can_add_self_assessment = serializers.SerializerMethodField()
    can_complete = serializers.SerializerMethodField()

    class Meta:
        model = Goal
        fields = (
            'id',
            'employee',
            'title',
            'description',
            'expected_results',
            'start_period',
            'end_period',
            'status',
            'status_display',
            'created_dttm',
            'updated_dttm',
            'progress_updates',
            'self_assessment',
            'can_be_submitted',
            'can_be_approved',
            'can_add_progress',
            'can_add_self_assessment',
            'can_complete'
        )
        read_only_fields = ('id', 'employee', 'created_dttm', 'updated_dttm')

    def get_can_be_submitted(self, obj):
        return obj.can_be_submitted()

    def get_can_be_approved(self, obj):
        return obj.can_be_approved()

    def get_can_add_progress(self, obj):
        return obj.can_add_progress()

    def get_can_add_self_assessment(self, obj):
        return obj.can_add_self_assessment()

    def get_can_complete(self, obj):
        return obj.can_complete()


class GoalCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Goal
        fields = (
            'id',
            'title',
            'description',
            'expected_results',
            'start_period',
            'end_period'
        )

    def validate(self, attrs):
        start_period = attrs.get('start_period')
        end_period = attrs.get('end_period')

        if start_period and end_period and start_period >= end_period:
            raise serializers.ValidationError(
                {"end_period": "Дата окончания должна быть позже даты начала."}
            )

        return attrs

    def create(self, validated_data):
        employee = self.context['request'].user.employee_profile

        goal = Goal.objects.create(
            employee=employee,
            status=Goal.STATUS_DRAFT,
            **validated_data
        )

        return goal


class GoalUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Goal
        fields = (
            'title', 'description', 'expected_results',
            'start_period', 'end_period'
        )

    def validate(self, attrs):
        instance = self.instance

        if instance.status != Goal.STATUS_DRAFT:
            raise serializers.ValidationError(
                "Обновлять можно только цели в статусе черновика."
            )

        start_period = attrs.get('start_period', instance.start_period)
        end_period = attrs.get('end_period', instance.end_period)

        if start_period and end_period and start_period >= end_period:
            raise serializers.ValidationError(
                {"end_period": "Дата окончания должна быть позже даты начала."}
            )

        return attrs
