from rest_framework import serializers
from .models import Regulation, AuditLog, StockSuspension, WorkingHours

class RegulationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Regulation
        fields = '__all__'


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = '__all__'


class StockSuspensionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockSuspension
        fields = '__all__'

class WorkingHoursSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkingHours
        fields = '__all__'