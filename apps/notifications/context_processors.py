from apps.notifications.services.selectors import NotificationSelector


def notifications(request):
    """Expose les notifications récentes et le compteur non-lu au topbar du dashboard,
    sans que chaque vue n'ait à les repasser explicitement dans son contexte."""
    if not request.user.is_authenticated:
        return {}
    recent = NotificationSelector.get_user_notifications(request.user)[:8]
    return {
        'notifications': recent,
        'unread_notifications_count': NotificationSelector.get_unread_count(request.user),
    }
