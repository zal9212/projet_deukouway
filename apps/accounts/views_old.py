from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.contrib.auth.views import LoginView as DjangoLoginView
from .forms import UserRegistrationForm, UserProfileForm
from django.contrib.auth import get_user_model

User = get_user_model()

class RegisterView(SuccessMessageMixin, CreateView):
    """
    User registration view handling roles and redirection logic.
    """
    model = User
    form_class = UserRegistrationForm
    template_name = 'pages/auth/register.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        user = form.save(commit=False)
        # If user registers as owner, initialize status to pending
        if user.role == 'owner':
            user.owner_status = 'pending'
            user.is_verified_owner = False
        else:
            user.owner_status = 'approved'
            user.is_verified_owner = False
            
        user.save()
        
        if user.role == 'owner':
            messages.success(self.request, "Inscription réussie ! Votre compte propriétaire est en cours de validation par l'administrateur.")
            return redirect('login')
        else:
            login(self.request, user)
            messages.success(self.request, f"Bienvenue sur DEKOUWAY, {user.first_name} !")
            return super().form_valid(form)


class LoginView(DjangoLoginView):
    """
    Authentication login view checking owner status verification.
    """
    template_name = 'pages/auth/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        user = form.get_user()
        if user.role == 'owner' and not user.is_verified_owner:
            if user.owner_status == 'pending':
                messages.warning(self.request, "Votre compte propriétaire est toujours en cours de validation par un administrateur.")
            elif user.owner_status == 'rejected':
                messages.error(self.request, "Votre compte propriétaire a été rejeté. Veuillez contacter le support.")
            return redirect('login')
        
        login(self.request, user)
        messages.success(self.request, f"Ravi de vous revoir, {user.first_name} !")
        return redirect(self.get_success_url())

    def get_success_url(self):
        user = self.request.user
        if user.role == 'owner':
            return reverse_lazy('owner_dashboard')
        elif user.role == 'admin' or user.is_superuser:
            return reverse_lazy('admin_dashboard')
        return reverse_lazy('home')


def logout_view(request):
    """
    Simple logout view handles POST or GET requests gracefully.
    """
    logout(request)
    messages.success(request, "Vous avez été déconnecté avec succès.")
    return redirect('home')


class ProfileView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """
    Update profile details for the authenticated user.
    """
    model = User
    form_class = UserProfileForm
    template_name = 'pages/client/profile.html'
    success_url = reverse_lazy('profile')
    success_message = "Profil mis à jour avec succès !"

    def get_object(self, queryset=None):
        return self.request.user
