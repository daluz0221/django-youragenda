from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeDoneView,
    PasswordChangeView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import FormView

from .forms import (
    EmailAuthenticationForm,
    EmailPasswordResetForm,
    SpanishPasswordChangeForm,
    SpanishSetPasswordForm,
    UserRegistrationForm,
)


class RegisterView(FormView):
    template_name = "registration/register.html"
    form_class = UserRegistrationForm

    def get_success_url(self):
        return settings.LOGIN_REDIRECT_URL

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect(self.get_success_url())


class EmailLoginView(LoginView):
    template_name = "registration/login.html"
    form_class = EmailAuthenticationForm
    redirect_authenticated_user = True


class EmailLogoutView(LogoutView):
    next_page = settings.LOGOUT_REDIRECT_URL


class EmailPasswordResetView(PasswordResetView):
    form_class = EmailPasswordResetForm
    template_name = "registration/password_reset_form.html"
    email_template_name = "registration/password_reset_email.html"
    subject_template_name = "registration/password_reset_subject.txt"
    success_url = reverse_lazy("accounts:password_reset_done")


class EmailPasswordResetDoneView(PasswordResetDoneView):
    template_name = "registration/password_reset_done.html"


class EmailPasswordResetConfirmView(PasswordResetConfirmView):
    form_class = SpanishSetPasswordForm
    template_name = "registration/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:password_reset_complete")


class EmailPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "registration/password_reset_complete.html"


class EmailPasswordChangeView(PasswordChangeView):
    form_class = SpanishPasswordChangeForm
    template_name = "registration/password_change_form.html"
    success_url = reverse_lazy("accounts:password_change_done")


class EmailPasswordChangeDoneView(PasswordChangeDoneView):
    template_name = "registration/password_change_done.html"
