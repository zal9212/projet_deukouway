from django.db.models import QuerySet, Q, Count
from apps.accounts.models import User, UserProfile, AuditUser, UserSession

class UserSelector:
    @staticmethod
    def get_user_by_email(email: str) -> User | None:
        return User.objects.filter(email=email).first()

    @staticmethod
    def get_user_by_id(user_id: str) -> User | None:
        return User.objects.filter(id=user_id, is_deleted=False).first()

    @staticmethod
    def get_all_users() -> QuerySet[User]:
        return User.objects.filter(is_deleted=False).order_by('-created_at')

    @staticmethod
    def get_all_active_users() -> QuerySet[User]:
        return User.objects.filter(is_active=True, is_deleted=False).order_by('-created_at')
        
    @staticmethod
    def get_active_users() -> QuerySet[User]:
        return User.objects.filter(is_active=True, is_deleted=False).order_by('-created_at')

    @staticmethod
    def get_all_clients(search_query: str = None, status: str = None) -> QuerySet[User]:
        qs = User.objects.filter(is_client=True, is_deleted=False).select_related('profile').annotate(
            reservations_count=Count('reservations', distinct=True)
        )
        if search_query:
            qs = qs.filter(
                Q(email__icontains=search_query) |
                Q(profile__first_name__icontains=search_query) |
                Q(profile__last_name__icontains=search_query) |
                Q(profile__phone__icontains=search_query)
            )
        if status == 'active':
            qs = qs.filter(is_active=True)
        elif status == 'blocked':
            qs = qs.filter(is_active=False)
        return qs.order_by('-created_at')

    @staticmethod
    def get_all_owners(search_query: str = None, status: str = None) -> QuerySet[User]:
        qs = User.objects.filter(is_owner=True, is_deleted=False).select_related('profile').annotate(
            properties_count=Count('properties', distinct=True)
        )
        if search_query:
            qs = qs.filter(
                Q(email__icontains=search_query) |
                Q(profile__first_name__icontains=search_query) |
                Q(profile__last_name__icontains=search_query) |
                Q(profile__phone__icontains=search_query)
            )
        if status == 'active':
            qs = qs.filter(is_verified=True)
        elif status == 'pending':
            qs = qs.filter(is_verified=False)
        return qs.order_by('-created_at')

    @staticmethod
    def get_pending_owners() -> QuerySet[User]:
        return User.objects.filter(is_owner=True, is_verified=False, is_deleted=False).prefetch_related('identity_documents').order_by('-created_at')

    @staticmethod
    def get_owner_profile(user_id: str) -> UserProfile | None:
        return UserProfile.objects.select_related('user').filter(user_id=user_id, user__is_owner=True).first()

    @staticmethod
    def get_user_profile(user: User) -> UserProfile | None:
        user_id = user.id if hasattr(user, 'id') else user
        profile, _ = UserProfile.objects.get_or_create(user_id=user_id)
        return profile

    @staticmethod
    def get_user_sessions(user_id: str) -> QuerySet[UserSession]:
        return UserSession.objects.filter(user_id=user_id).order_by('-last_activity')

    @staticmethod
    def get_user_audit_logs(user_id: str) -> QuerySet[AuditUser]:
        return AuditUser.objects.filter(user_id=user_id).order_by('-created_at')

    @staticmethod
    def get_all_audit_logs() -> QuerySet[AuditUser]:
        return AuditUser.objects.select_related('user').all().order_by('-created_at')
