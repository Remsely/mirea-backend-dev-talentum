from rest_framework import serializers

from .models import SelfAssessment


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