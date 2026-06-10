from tools.required_role import RoleRequiredMixin

from .forms import (
    CustomPasswordResetForm,
    LoginForm,
    SignupForm,
)
from django.urls import reverse_lazy

from django.contrib.auth.views import LoginView, PasswordResetView
from django.views.generic import CreateView, ListView, View
from django.shortcuts import get_object_or_404, render, redirect
from .models import Profile
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.contrib import messages
from datetime import datetime
from django.contrib.auth import logout
from PIL import Image, UnidentifiedImageError
from django.contrib.auth import get_user_model


# Clock and Unclock account
class UserActiveToggleView(RoleRequiredMixin, View):
    allowed_roles = ["admin"]

    def post(self, request, *args, **kwargs):

        user_id = kwargs["user_id"]

        User = get_user_model()

        user = get_object_or_404(
            User,
            id=user_id,
        )

        if user.is_superuser:
            messages.error(request, "Không thể khóa Superuser.")
            return redirect("user_list")

        user.is_active = not user.is_active

        user.save(update_fields=["is_active"])

        messages.success(request, "Cập nhật trạng thái tài khoản thành công.")

        return redirect("user_list")


# Update permission
class UserRoleUpdateView(RoleRequiredMixin, View):
    allowed_roles = ["admin"]

    def post(self, request, *args, **kwargs):
        user_id = kwargs["user_id"]
        User = get_user_model()
        user = get_object_or_404(User, id=user_id)

        if user.is_superuser:
            messages.error(request, "Không thể đổi quyền SuperUser")
            return redirect("user_list")
        if user.role == "customer":
            user.role = "staff"
            user.is_staff = True
        elif user.role == "staff":
            user.role = "customer"
            user.is_staff = False
        user.save()
        messages.success(request, "Cập nhật quyền thành công")

        return redirect("user_list")


# List user


class UserListView(RoleRequiredMixin, ListView):
    model = get_user_model()
    template_name = "core/user_list.html"
    context_object_name = "users"
    allowed_roles = ["admin"]

    def get_queryset(self):
        return self.model.objects.select_related("profile").order_by("-date_joined")


# profile
@login_required
def profile_view(request):
    """Hiển thị trang profile"""
    user_profile = Profile.objects.filter(user=request.user).first()
    context = {
        "user": request.user,
        "profile": user_profile,
    }
    return render(request, "registration/profile.html", context)


@login_required
@require_http_methods(["POST"])
def edit_profile(request):
    try:
        user = request.user
        profile, created = Profile.objects.get_or_create(user=user)

        if "name" in request.POST:
            user.name = request.POST.get("name", "")
            user.save()

        profile.phone = request.POST.get("phone", "") or None
        profile.address = request.POST.get("address", "") or None
        profile.sex = request.POST.get("sex", "") or None  # type: ignore
        profile.bio = request.POST.get("bio", "") or None

        # Xử lý birthday
        birthday = request.POST.get("birthday", "")
        if birthday:
            try:
                profile.birthday = datetime.strptime(birthday, "%Y-%m-%d").date()
            except:
                profile.birthday = None
        else:
            profile.birthday = None

        profile.save()

        return JsonResponse(
            {
                "success": True,
                "message": "Your information has been successfully submitted!",
            }
        )

    except Exception as e:
        return JsonResponse({"success": False, "message": f"Lỗi: {str(e)}"}, status=500)


@login_required
@require_http_methods(["POST"])
def upload_avatar(request):
    try:
        if "avatar" not in request.FILES:
            return JsonResponse(
                {"success": False, "message": "Không tìm thấy file ảnh"}, status=400
            )

        avatar_file = request.FILES["avatar"]

        if not avatar_file.content_type.startswith("image/"):
            return JsonResponse(
                {"success": False, "message": "File phải là hình ảnh"}, status=400
            )

        if avatar_file.size > 5 * 1024 * 1024:
            return JsonResponse(
                {"success": False, "message": "Ảnh tối đa 5MB"}, status=400
            )

        try:
            Image.open(avatar_file).verify()
        except (UnidentifiedImageError, OSError):
            return JsonResponse(
                {"success": False, "message": "File ảnh không hợp lệ"}, status=400
            )
        finally:
            avatar_file.seek(0)

        profile, created = Profile.objects.get_or_create(user=request.user)

        profile.avatar = avatar_file
        profile.save()

        return JsonResponse(
            {
                "success": True,
                "avatar_url": profile.avatar.url,
                "message": "Cập nhật avatar thành công!",
            }
        )

    except Exception as e:
        return JsonResponse(
            {
                "success": False,
                "message": f"Lỗi: {str(e)}",
                "error_type": type(e).__name__,
            },
            status=500,
        )


class LoginCustomView(LoginView):
    template_name = "registration/login.html"
    authentication_form = LoginForm

    def get_success_url(self):
        user = self.request.user
        if user.is_superuser or user.role == "admin":  # type: ignore
            return reverse_lazy("store:admin_dashboard")
        if user.role == "staff":  # type: ignore
            return reverse_lazy("store:staff_dashboard")
        else:
            return reverse_lazy("store:customer_dashboard")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("store:home")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Login"
        return context


@login_required
def logout_view(request):
    logout(request)
    # messages.success(request, "Logout success!!!!!!")
    return redirect("account_login")


class SignupView(CreateView):
    form_class = SignupForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("account_login")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Đăng ký tài khoản"
        return context

    def form_valid(self, form):
        messages.success(self.request, "Đăng ký tài khoản thành công!")
        return super().form_valid(form)


class CustomPasswordResetView(PasswordResetView):
    form_class = CustomPasswordResetForm
    template_name = "registration/password_reset_form.html"
    email_template_name = "registration/password_reset_email.html"
    success_url = reverse_lazy("password_reset_done")
