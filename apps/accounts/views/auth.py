import logging
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView, PasswordResetConfirmView
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.tokens import default_token_generator
from django import forms
from django.views.generic import FormView, TemplateView, View
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import login, get_user_model
from django.db import transaction
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from apps.core.mixins import ViewExceptionHandlingMixin
from apps.accounts.forms import ClientRegistrationForm, OwnerRegistrationForm
from apps.accounts.services.services import AccountService
from apps.accounts.services.selectors import UserSelector
from apps.accounts.services.exceptions import UserAlreadyExists

User = get_user_model()
logger = logging.getLogger(__name__)


class EmailAuthenticationForm(AuthenticationForm):
    """Formulaire de connexion utilisant email + mot de passe."""
    username = forms.EmailField(
        label="Adresse e-mail",
        widget=forms.EmailInput(attrs={
            'autocomplete': 'email',
            'placeholder': 'votre@email.com',
            'required': 'required',
        })
    )

class RegisterChoiceView(TemplateView):
    template_name = 'pages/auth/register_choice.html'

class CustomLoginView(ViewExceptionHandlingMixin, LoginView):
    template_name = 'pages/auth/login.html'
    authentication_form = EmailAuthenticationForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        messages.success(self.request, "Connexion réussie. Bienvenue sur DEKOUWAY !")
        return super().form_valid(form)

    def form_invalid(self, form):
        attempted_email = form.data.get('username', '')
        client_ip = self.request.META.get('REMOTE_ADDR', 'inconnu')
        # %r (repr) échappe les retours à la ligne au lieu de les insérer tels
        # quels : sans ça, un champ "username" contenant \r\n permettrait
        # d'injecter de fausses lignes dans les logs (l'entrée n'est pas
        # encore validée à ce stade). Tronqué par précaution, la donnée n'étant
        # pas bornée en longueur avant validation.
        logger.warning("Échec de connexion pour %r depuis %s", attempted_email[:254], client_ip)
        messages.error(self.request, "Identifiants invalides. Veuillez réessayer.")
        return super().form_invalid(form)

    def get_success_url(self):
        user = self.request.user
        if getattr(user, 'is_superadmin', False) or user.is_staff or user.is_superuser:
            return reverse_lazy('dashboard:admin_home')
        elif getattr(user, 'is_owner', False):
            return reverse_lazy('dashboard:owner_home')
        return reverse_lazy('dashboard:client_home')

class CustomLogoutView(ViewExceptionHandlingMixin, LogoutView):
    next_page = reverse_lazy('public:home')

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        messages.info(request, "Vous avez été déconnecté avec succès.")
        return response

class ClientRegisterView(ViewExceptionHandlingMixin, FormView):
    template_name = 'pages/auth/register_client.html'
    form_class = ClientRegistrationForm
    success_url = reverse_lazy('dashboard:client_home')

    def form_valid(self, form):
        email = form.cleaned_data['email']
        password = form.cleaned_data['password1']
        first_name = form.cleaned_data['first_name']
        last_name = form.cleaned_data['last_name']

        try:
            user = AccountService.register_client(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(self.request, "Votre compte client a été créé avec succès !")
            return redirect(self.get_success_url())
        except UserAlreadyExists as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)

class OwnerRegisterView(ViewExceptionHandlingMixin, FormView):
    template_name = 'pages/auth/register_owner.html'
    form_class = OwnerRegistrationForm
    success_url = reverse_lazy('accounts:owner_pending')

    def form_valid(self, form):
        email = form.cleaned_data['email']
        password = form.cleaned_data['password1']
        first_name = form.cleaned_data['first_name']
        last_name = form.cleaned_data['last_name']

        try:
            with transaction.atomic():
                user = AccountService.register_owner(
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name
                )
                AccountService.upload_identity_document(
                    user=user,
                    document_type=form.cleaned_data['document_type'],
                    document_number=form.cleaned_data['document_number'],
                    file=form.cleaned_data['identity_file'],
                    file_back=form.cleaned_data.get('identity_file_back'),
                    selfie_file=form.cleaned_data['selfie_with_id_file'],
                )
            messages.info(self.request, "Votre inscription propriétaire est enregistrée. Un administrateur va valider votre dossier.")
            return redirect(self.get_success_url())
        except UserAlreadyExists as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)

class VerifyEmailView(ViewExceptionHandlingMixin, View):
    def get(self, request, *args, **kwargs):
        uid = request.GET.get('uid', '')
        token = request.GET.get('token', '')
        user = None
        try:
            user_pk = force_str(urlsafe_base64_decode(uid))
            user = UserSelector.get_user_by_id(user_pk)
        except (TypeError, ValueError, OverflowError):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            AccountService.verify_email(user)
            messages.success(request, "Votre adresse email a été vérifiée avec succès !")
            return redirect('accounts:login')

        messages.error(request, "Lien de vérification invalide ou expiré.")
        return redirect('public:home')

class CustomPasswordResetView(ViewExceptionHandlingMixin, PasswordResetView):
    template_name = 'pages/auth/forgot_password.html'
    email_template_name = 'pages/auth/password_reset_email.html'
    success_url = reverse_lazy('accounts:password_reset_done')

    def form_valid(self, form):
        messages.info(self.request, "Si cette adresse email existe, un lien de réinitialisation vous a été envoyé.")
        return super().form_valid(form)

class CustomPasswordResetConfirmView(ViewExceptionHandlingMixin, PasswordResetConfirmView):
    template_name = 'pages/auth/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:login')

    def form_valid(self, form):
        # form.save() (SetPasswordForm) ferait déjà set_password()+save() : on ne
        # l'appelle pas et on passe directement par le service, seule source de
        # vérité pour la mutation, plutôt que d'écrire le mot de passe deux fois.
        AccountService.change_password(form.user, form.cleaned_data['new_password1'])
        messages.success(self.request, "Votre mot de passe a été réinitialisé avec succès. Vous pouvez vous connecter.")
        return redirect(self.success_url)

class OwnerPendingView(ViewExceptionHandlingMixin, TemplateView):
    template_name = 'pages/auth/owner_pending.html'
