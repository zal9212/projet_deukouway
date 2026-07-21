from django.db.models import QuerySet
from apps.dashboard.models import AuditLog, ActivityLog, SystemLog

class DashboardSelector:
    
    @staticmethod
    def get_recent_activity(user_id: str, limit: int = 10) -> QuerySet[ActivityLog]:
        return ActivityLog.objects.filter(user_id=user_id).order_by('-created_at')[:limit]
        
    @staticmethod
    def get_system_logs(limit: int = 50) -> QuerySet[SystemLog]:
        return SystemLog.objects.all().order_by('-created_at')[:limit]
