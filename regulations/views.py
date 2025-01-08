from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Regulation, AuditLog, StockSuspension,WorkingHours
from .serializers import RegulationSerializer, AuditLogSerializer, StockSuspensionSerializer,WorkingHoursSerializer
from django.utils.timezone import now

class RegulationViewSet(viewsets.ModelViewSet):
    queryset = Regulation.objects.all()
    serializer_class = RegulationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        regulation = serializer.save(created_by=request.user)
        AuditLog.objects.create(
            action=f"Created regulation {regulation.name}",
            performed_by=request.user,
            details=f"Value: {regulation.value}"
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer

class WorkingHoursViewSet(viewsets.ModelViewSet):
    queryset = WorkingHours.objects.all()
    serializer_class = WorkingHoursSerializer

class StockSuspensionViewSet(viewsets.ModelViewSet):
    queryset = StockSuspension.objects.all()
    serializer_class = StockSuspensionSerializer

    @action(detail=True, methods=['post'])
    def release(self, request, pk=None):
        suspension = self.get_object()
        if not suspension.is_active:
            return Response({"error": "Suspension is already inactive."}, status=status.HTTP_400_BAD_REQUEST)
        suspension.is_active = False
        suspension.released_at = now()
        suspension.save()
        return Response({"message": "Suspension released successfully."})

    def create(self, request, *args, **kwargs):
        """
        Custom creation logic to handle both specific and full suspensions.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        suspension = serializer.save()

        # Notify the trader if required (add notification logic here if applicable)
        return Response(serializer.data, status=status.HTTP_201_CREATED)