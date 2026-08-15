import logging

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

logger = logging.getLogger(__name__)


class AccountAdapter(DefaultAccountAdapter):
    """
    On ne veut PAS du formulaire d'inscription générique d'allauth (il ne crée
    pas de UserProfile et contournerait nos flux d'inscription client/hôte
    dédiés). Seule la connexion sociale (Google) reste ouverte : voir
    SocialAccountAdapter.is_open_for_signup, qui ne délègue pas ici.
    """
    def is_open_for_signup(self, request):
        return False


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Adapte la connexion sociale (Google) à notre modèle User custom :
    - pas de champ `username` ;
    - un rôle (is_client/is_owner) obligatoire ;
    - un UserProfile séparé (prénom/nom) requis par le reste de l'app.

    Un nouveau compte créé via Google est toujours un compte VOYAGEUR
    (is_client=True). Devenir hôte reste un choix explicite via le formulaire
    dédié (apps/accounts/views/auth.py:OwnerRegisterView), qui déclenche en
    plus un vrai parcours de vérification KYC — on ne veut pas qu'un simple
    clic Google puisse l'accorder silencieusement.
    """

    def is_open_for_signup(self, request, sociallogin):
        return True

    def on_authentication_error(self, request, provider, error=None, exception=None, extra_context=None):
        # allauth affiche une page d'erreur générique sans jamais logger la cause
        # réelle (échec d'échange de token, client_secret invalide, etc.) : on la
        # journalise nous-mêmes pour pouvoir diagnostiquer un échec de connexion Google.
        logger.exception(
            f"Échec de connexion Google (error={error}) : {exception}",
            exc_info=exception,
        )

    def save_user(self, request, sociallogin, form=None):
        from apps.accounts.models import UserProfile

        user = sociallogin.user
        user.set_unusable_password()
        user.is_client = True
        user.is_owner = False
        # Google a déjà vérifié la propriété de cette adresse email.
        user.email_verified = True
        sociallogin.save(request)

        UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'first_name': user.first_name or '',
                'last_name': user.last_name or '',
            },
        )
        return user
