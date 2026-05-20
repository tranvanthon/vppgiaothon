from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("login/", views.LoginCustomView.as_view(), name="account_login"),
    path("signup/", views.SignupView.as_view(), name="account_signup"),
    path("logout/", views.logout_view, name="account_logout"),
    path("profile/", views.profile_view, name="profile"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    path("profile/upload-avatar/", views.upload_avatar, name="upload_avatar"),
    path(
        "password/reset/",
        views.CustomPasswordResetView.as_view(),
        name="password_reset",
    ),
    path(
        "password/reset/done/",
        auth_views.PasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    path("password/change/", auth_views.PasswordChangeView.as_view(), name="password_change"),
    path(
        "password/change/done/",
        auth_views.PasswordChangeDoneView.as_view(),
        name="password_change_done",
    ),

]
