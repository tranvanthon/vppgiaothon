from django.core.exceptions import PermissionDenied

class RoleRequiredMixin:
    allowed_roles = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied()

        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)

        if request.user.role in self.allowed_roles:
            return super().dispatch(request, *args, **kwargs)

        raise PermissionDenied()