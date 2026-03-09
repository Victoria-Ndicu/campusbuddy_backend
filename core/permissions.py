from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwnerOrAdmin(BasePermission):
    """
    Object-level permission: allow access only to the owner of an object or admin users.
    The object must expose an `owner` property or attribute.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff or request.user.role == "admin":
            return True
        owner = getattr(obj, "owner", None) or getattr(obj, "user", None)
        return owner == request.user


class IsOwnerOrReadOnly(BasePermission):
    """
    Object-level permission: read-only for any authenticated user, write only for owner.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        owner = getattr(obj, "owner", None) or getattr(obj, "user", None)
        return owner == request.user


class IsAdminUser(BasePermission):
    """Allow access only to users with role = 'admin'."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.role == "admin")