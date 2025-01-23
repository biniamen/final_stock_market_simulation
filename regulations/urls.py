from rest_framework.routers import DefaultRouter
from .views import RegulationViewSet, AuditLogViewSet, StockSuspensionViewSet, WorkingHoursViewSet
from django.urls import include, path

router = DefaultRouter()
router.register(r'regulations', RegulationViewSet, basename='regulation')
router.register(r'audit-logs', AuditLogViewSet, basename='audit-log')
router.register(r'suspensions', StockSuspensionViewSet, basename='suspension')
router.register(r'working-hours', WorkingHoursViewSet, basename='working-hours')



urlpatterns = [
    path('', include(router.urls)),
]