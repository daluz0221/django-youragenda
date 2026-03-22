from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.EmailLoginView.as_view(), name="login"),
    path("logout/", views.EmailLogoutView.as_view(), name="logout"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path(
        "password-change/",
        views.EmailPasswordChangeView.as_view(),
        name="password_change",
    ),
    path(
        "password-change/done/",
        views.EmailPasswordChangeDoneView.as_view(),
        name="password_change_done",
    ),
    path(
        "password-reset/",
        views.EmailPasswordResetView.as_view(),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        views.EmailPasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "reset/done/",
        views.EmailPasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    path(
        "reset/<uidb64>/<token>/",
        views.EmailPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
]
