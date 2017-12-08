from rest_framework import permissions


class ActivateFirstIfInactive(permissions.BasePermission):
    """Object level permission that will disallow editing user data
    until user is active.

    Admin can send requests that contains "is_active": True with additional
    data and request will succeed, but if is_active not present in request and
    user is inactive PermissionDenied will be raised.
    """
    message = (
        'Editing inactive user state is not allowed. Activate user first'
    )

    def has_object_permission(self, request, view, obj):
        if request.method not in permissions.SAFE_METHODS and not obj.is_active:
            status = request.data.get('is_active')
            return status is not None and status
        return True

class CantEditSuperuserIfNotSuperuser(permissions.BasePermission):
    """Object level permission that will disallow editing superuser data
    until user that submiting changes is superuser
    """
    message = 'You can\'t edit this user data'

    def has_object_permission(self, request, view, obj):
        if request.method not in permissions.SAFE_METHODS and obj.is_superuser:
            return request.user.is_superuser
        return True
