from django.db import transaction
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from apps.accounts.models import User, UserProfile, IdentityDocument
from apps.accounts.services.exceptions import UserAlreadyExists, InvalidRoleException
from apps.accounts.services.selectors import UserSelector
import logging

logger = logging.getLogger(__name__)

class AccountService:
    
    @staticmethod
    @transaction.atomic
    def register_client(email: str, password: str, first_name: str, last_name: str) -> User:
        """Enregistre un nouvel utilisateur client."""
        if UserSelector.get_user_by_email(email):
            raise UserAlreadyExists(f"L'utilisateur avec l'email {email} existe déjà.")
            
        user = User.objects.create_user(email=email, password=password, is_client=True, is_owner=False)
        UserProfile.objects.create(user=user, first_name=first_name, last_name=last_name)
        
        logger.info(f"Client inscrit : {email}")
        return user

    @staticmethod
    @transaction.atomic
    def register_owner(email: str, password: str, first_name: str, last_name: str) -> User:
        """Enregistre un nouvel utilisateur propriétaire."""
        if UserSelector.get_user_by_email(email):
            raise UserAlreadyExists(f"L'utilisateur avec l'email {email} existe déjà.")
            
        # is_active reste True : le propriétaire doit pouvoir se connecter dès l'inscription.
        # is_verified (défaut False) bloque uniquement la publication de logements, tant que
        # le SuperAdmin n'a pas validé sa pièce d'identité.
        user = User.objects.create_user(email=email, password=password, is_client=False, is_owner=True)
        UserProfile.objects.create(user=user, first_name=first_name, last_name=last_name)
        
        logger.info(f"Propriétaire inscrit et en attente d'approbation : {email}")
        return user

    @staticmethod
    @transaction.atomic
    def approve_owner(user: User, admin_user: User) -> User:
        """Approuve un compte propriétaire (Action SuperAdmin)."""
        if not user.is_owner:
            raise InvalidRoleException("L'utilisateur n'est pas un propriétaire.")

        user.is_verified = True
        user.save(update_fields=['is_verified'])
        logger.info(f"Propriétaire {user.email} approuvé par {admin_user.email}")
        return user

    @staticmethod
    @transaction.atomic
    def reject_owner(user: User, admin_user: User) -> User:
        """Rejette un compte propriétaire (Action SuperAdmin)."""
        if not user.is_owner:
            raise InvalidRoleException("L'utilisateur n'est pas un propriétaire.")
        user.soft_delete()
        logger.info(f"Propriétaire {user.email} rejeté par {admin_user.email}")
        return user

    @staticmethod
    @transaction.atomic
    def activate_account(user: User) -> User:
        user.is_active = True
        user.save(update_fields=['is_active'])
        return user

    @staticmethod
    @transaction.atomic
    def deactivate_account(user: User) -> User:
        user.is_active = False
        user.save(update_fields=['is_active'])
        return user

    @staticmethod
    @transaction.atomic
    def block_user(user: User, admin_user: User) -> User:
        user.is_active = False
        user.save(update_fields=['is_active'])
        logger.warning(f"Utilisateur {user.email} bloqué par {admin_user.email}")
        return user

    @staticmethod
    @transaction.atomic
    def unblock_user(user: User, admin_user: User) -> User:
        user.is_active = True
        user.save(update_fields=['is_active'])
        logger.info(f"Utilisateur {user.email} débloqué par {admin_user.email}")
        return user

    @staticmethod
    @transaction.atomic
    def change_password(user: User, new_password: str) -> User:
        user.set_password(new_password)
        user.save()
        logger.info(f"Mot de passe modifié pour l'utilisateur {user.email}")
        return user

    @staticmethod
    @transaction.atomic
    def change_email(user: User, new_email: str) -> User:
        if UserSelector.get_user_by_email(new_email):
            raise UserAlreadyExists("Cet email est déjà utilisé.")
        user.email = new_email
        user.save(update_fields=['email'])
        logger.info(f"Email modifié pour l'utilisateur vers {new_email}")
        return user

    @staticmethod
    def generate_email_verification_token(user: User) -> tuple:
        """Génère un couple (uid, token) signé et à usage unique pour la vérification d'email."""
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        return uid, token

    @staticmethod
    @transaction.atomic
    def verify_email(user: User) -> bool:
        user.email_verified = True
        user.save(update_fields=['email_verified'])
        logger.info(f"Email vérifié pour l'utilisateur {user.email}")
        return True

    @staticmethod
    @transaction.atomic
    def verify_phone(user: User) -> bool:
        # Logique métier pour vérifier le téléphone
        logger.info(f"Téléphone vérifié pour l'utilisateur {user.email}")
        return True

    @staticmethod
    @transaction.atomic
    def upload_identity_document(user: User, document_type: str, document_number: str, file, selfie_file=None, file_back=None) -> IdentityDocument:
        doc = IdentityDocument.objects.create(
            user=user,
            document_type=document_type,
            document_number=document_number,
            file=file,
            file_back=file_back,
            selfie_file=selfie_file
        )
        logger.info(f"Document d'identité (+ verso: {bool(file_back)}, + selfie: {bool(selfie_file)}) téléchargé pour l'utilisateur {user.email}")
        return doc
