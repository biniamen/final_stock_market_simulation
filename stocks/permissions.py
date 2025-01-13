# stocks/permissions.py

from rest_framework.permissions import BasePermission

class IsRegulatorUser(BasePermission):
    """
    Allows access only to users with role='regulator'.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'regulator')
