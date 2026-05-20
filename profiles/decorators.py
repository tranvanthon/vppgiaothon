from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.conf import settings


def role_required(allowed_roles=None):
    if allowed_roles is None:
        allowed_roles = []

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):

            # Chưa login → redirect
            if not request.user.is_authenticated:
                return redirect(settings.LOGIN_URL)

            # Superuser bypass
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            # Check role
            if request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)

            raise PermissionDenied

        return _wrapped_view

    return decorator