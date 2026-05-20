from django.views.generic import UpdateView, DetailView, CreateView
from .decorators import role_required

from .forms import (
    CustomPasswordResetForm,
    LoginForm,
    SignupForm,
    CustomPasswordChangeForm,
)
from django.urls import reverse_lazy

from django.contrib.auth.views import LoginView, PasswordChangeView, PasswordResetView
from django.shortcuts import render, redirect
from .models import Profile
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
import traceback
from datetime import datetime
from django.contrib.auth import logout


@login_required
def profile_view(request):
    """Hiển thị trang profile"""
    profile = Profile.objects.all().values()
    context = {"user": request.user, "profile": profile}
    return render(request, "registration/profile.html", context)


@login_required
@require_http_methods(["POST"])
def edit_profile(request):
    try:
        user = request.user
        profile, created = Profile.objects.get_or_create(user=user)
        if created:
            print("Auto-created profile for {user.email} via get_or_create")
        if "name" in request.POST:
            user.name = request.POST.get("name", "")
            user.save()
        profile.phone = request.POST.get("phone", "") or None
        profile.address = request.POST.get("address", "") or None
        profile.sex = request.POST.get("sex", "") or None
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
        print(f"Error in edit_profile: {e}")
        traceback.print_exc()
        return JsonResponse({"success": False, "message": f"Lỗi: {str(e)}"}, status=500)


@login_required
@require_http_methods(["POST"])  # Chỉ cho phép POST
def upload_avatar(request):
    try:
        # Kiểm tra file có tồn tại không
        if "avatar" not in request.FILES:
            print("ERROR: No 'avatar' in request.FILES")
            return JsonResponse(
                {"success": False, "message": "Không tìm thấy file ảnh"}, status=400
            )
        avatar_file = request.FILES["avatar"]
        print(
            f"File found: {avatar_file.name}, size: {avatar_file.size}, type: {avatar_file.content_type}"
        )
        # Kiểm tra profile có tồn tại không
        try:
            profile = request.user.profile
            print(f"Profile exists: {profile}")
        except Exception as e:
            print(f"Profile error: {e}")
            profile = Profile.objects.create(user=request.user)
            print(f"Created new profile: {profile}")
        # Save avatar
        profile.avatar = avatar_file
        profile.save()
        print(f"Avatar saved successfully!")
        print(f"Avatar URL: {profile.avatar.url}")

        return JsonResponse(
            {
                "success": True,
                "avatar_url": profile.avatar.url,
                "message": "Cập nhật avatar thành công!",
            }
        )

    except Exception as e:
        print("\n" + "!" * 60)
        print("ERROR OCCURRED:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print("\nTraceback:")
        traceback.print_exc()
        print("!" * 60 + "\n")

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
        if user.is_superuser or user.role == "admin":
            return reverse_lazy("store:admin_dashboard")
        if user.role == "staff":
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
