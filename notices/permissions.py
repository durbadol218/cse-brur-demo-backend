# Create a new file: permissions.py (in the same app directory)

from rest_framework.permissions import BasePermission

class IsAdminOrFaculty(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['admin', 'faculty']

class CanDownloadNotice(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['admin', 'faculty', 'student', 'alumni', 'staff']