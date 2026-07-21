from django.contrib.auth.views import LoginView as BaseLoginView, LogoutView as BaseLogoutView, PasswordResetView, PasswordResetConfirmView
from django.views.generic import FormView, TemplateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect
from apps.accounts.forms import RegistrationForm
from apps.accounts.services.services import AccountService
from apps.accounts.services.exceptions import UserAlreadyExists

class CustomLoginView(BaseLoginView):
    template_name = 'pages/auth/login.html'
    
    def get_success_url(self):
        if self.request.user.is_superuser or self.request.user.is_staff:
            return reverse_lazy('dashboard:admin_home')
        elif self.request.user.is_owner:
            return reverse_lazy('dashboard:owner_home')
        return reverse_lazy('dashboard:client_home')

class CustomLogoutView(BaseLogoutView):
    next_page = 'public:home'

class ClientRegisterView(FormView):
    template_name = 'pages/auth/register_client.html'
    form_class = RegistrationForm
    success_url = reverse_lazy('accounts:login')

    def form_valid(self, form):
        data = form.cleaned_data
        try:
            AccountService.register_client(
                email=data['email'],
                password=data['password'],
                first_name=data['first_name'],
                last_name=data['last_name']
            )
            messages.success(self.request, "Compte locataire créé avec succès. Vous pouvez vous connecter.")
            return super().form_valid(form)
        except UserAlreadyExists as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)

class OwnerRegisterView(FormView):
    template_name = 'pages/auth/register_owner.html'
    form_class = RegistrationForm
    success_url = reverse_lazy('accounts:owner_pending')

    def form_valid(self, form):
        data = form.cleaned_data
        try:
            AccountService.register_owner(
                email=data['email'],
                password=data['password'],
                first_name=data['first_name'],
                last_name=data['last_name']
            )
            messages.success(self.request, "Compte propriétaire créé. Il est en attente de validation.")
            return super().form_valid(form)
        except UserAlreadyExists as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)

class OwnerPendingView(TemplateView):
    template_name = 'pages/auth/owner_pending.html'

class CustomPasswordResetView(PasswordResetView):
    template_name = 'pages/auth/password_reset.html'
    success_url = reverse_lazy('accounts:password_reset_done')

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'pages/auth/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:login')
