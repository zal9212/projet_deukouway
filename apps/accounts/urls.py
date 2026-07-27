from django.urls import path
from django.contrib.auth.views import PasswordResetDoneView
from .views.auth import (
    CustomLoginView, CustomLogoutView, ClientRegisterView,
    OwnerRegisterView, RegisterChoiceView, VerifyEmailView, OwnerPendingView,
    CustomPasswordResetView, CustomPasswordResetConfirmView
)
from .views.documents import IdentityDocumentFileView

app_name = 'accounts'

urlpatterns = [
    path('documents-identite/<uuid:doc_id>/<str:field>/', IdentityDocumentFileView.as_view(), name='identity_document_file'),
    path('se-connecter/', CustomLoginView.as_view(), name='login'),
    path('se-deconnecter/', CustomLogoutView.as_view(), name='logout'),
    path('rejoindre/', RegisterChoiceView.as_view(), name='register_choice'),
    path('rejoindre/voyageur/', ClientRegisterView.as_view(), name='register_client'),
    path('rejoindre/hote/', OwnerRegisterView.as_view(), name='register_owner'),
    path('verification/', VerifyEmailView.as_view(), name='verify_email'),
    path('validation-compte/', OwnerPendingView.as_view(), name='owner_pending'),
    path('securite/reinitialisation/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('mot-de-passe/oublie/', CustomPasswordResetView.as_view(), name='forgot_password'),
    path('securite/reinitialisation/envoye/', PasswordResetDoneView.as_view(template_name='pages/auth/password_reset_done.html'), name='password_reset_done'),
    path('securite/nouveau-mot-de-passe/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
]
