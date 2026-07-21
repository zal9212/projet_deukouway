from django.db.models import QuerySet
from apps.accounts.models import User, UserProfile

class UserSelector:
    @staticmethod
    def get_user_by_email(email: str) -> User | None:
        return User.objects.filter(email=email).first()
        
    @staticmethod
    def get_active_users() -> QuerySet[User]:
        return User.objects.filter(is_active=True, is_deleted=False)

    @staticmethod
    def get_owner_profile(user_id: str) -> UserProfile | None:
        return UserProfile.objects.select_related('user').filter(user_id=user_id, user__is_owner=True).first()
