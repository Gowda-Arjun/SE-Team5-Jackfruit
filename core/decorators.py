from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def role_required(*roles):
    """Allow the view only for users whose role is in `roles`; others get 403.

    Usage:  @role_required(User.Role.WARDEN, User.Role.ADMIN)
    HMS-F-005 / HMS-SR-003 extend this with audit logging of denied attempts.
    """

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.role not in roles:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator
