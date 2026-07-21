from django.urls import path
from django.contrib.auth.views import PasswordResetDoneView
from .views.auth import (
    CustomLoginView, CustomLogoutView, ClientRegisterView, 
    OwnerRegisterView, OwnerPendingView, CustomPasswordResetView,
    CustomPasswordResetConfirmView
)

app_name = 'accounts'

urlpatterns = [
    path('connexion/', CustomLoginView.as_view(), name='login'),
    path('deconnexion/', CustomLogoutView.as_view(), name='logout'),
    path('inscription/client/', ClientRegisterView.as_view(), name='register_client'),
    path('inscription/proprietaire/', OwnerRegisterView.as_view(), name='register_owner'),
    path('proprietaire/en-attente/', OwnerPendingView.as_view(), name='owner_pending'),
    
    path('mot-de-passe/oublie/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('mot-de-passe/oublie/envoye/', PasswordResetDoneView.as_view(template_name='pages/auth/password_reset_done.html'), name='password_reset_done'),
    path('mot-de-passe/reinitialisation/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
]
