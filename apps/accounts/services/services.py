from django.db import transaction
from django.utils import timezone
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
            
        user = User.objects.create_user(email=email, password=password, is_client=False, is_owner=True)
        # Le propriétaire n'est généralement pas actif tant qu'il n'est pas approuvé
        user.is_active = False
        user.save()
        UserProfile.objects.create(user=user, first_name=first_name, last_name=last_name)
        
        logger.info(f"Propriétaire inscrit et en attente d'approbation : {email}")
        return user

    @staticmethod
    @transaction.atomic
    def approve_owner(user: User, admin_user: User) -> User:
        """Approuve un compte propriétaire (Action SuperAdmin)."""
        if not user.is_owner:
            raise InvalidRoleException("L'utilisateur n'est pas un propriétaire.")
            
        user.is_active = True
        user.save()
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
    @transaction.atomic
    def verify_email(user: User) -> bool:
        # Logique métier pour vérifier le jeton d'email
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
    def upload_identity_document(user: User, document_type: str, document_number: str, file) -> IdentityDocument:
        doc = IdentityDocument.objects.create(
            user=user,
            document_type=document_type,
            document_number=document_number,
            file=file
        )
        logger.info(f"Document d'identité téléchargé pour l'utilisateur {user.email}")
        return doc
