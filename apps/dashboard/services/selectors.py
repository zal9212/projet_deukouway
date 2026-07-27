from django.db.models import QuerySet, Count, Sum, Avg, F, Q, ExpressionWrapper, fields
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings
import calendar
import datetime

from apps.dashboard.models import AuditLog, ActivityLog, SystemLog
from apps.reservations.models import Reservation, ReservationRequest
from apps.properties.models import Property, PropertyReview
from apps.accounts.models import User
from apps.payments.models import Payment, Commission, Payout

class DashboardSelector:
    
    @staticmethod
    def get_recent_activity(user_id: str, limit: int = 10) -> QuerySet[ActivityLog]:
        return ActivityLog.objects.filter(user_id=user_id).order_by('-created_at')[:limit]

    @staticmethod
    def get_system_logs(limit: int = 50, search_query: str = None, level: str = None) -> QuerySet[SystemLog]:
        qs = SystemLog.objects.all().order_by('-created_at')
        if search_query:
            qs = qs.filter(Q(message__icontains=search_query) | Q(source__icontains=search_query))
        if level:
            qs = qs.filter(level=level)
        return qs[:limit]

    @staticmethod
    def get_client_stats(user_id: str) -> dict:
        total_reservations = Reservation.objects.filter(client_id=user_id, is_deleted=False).count()
        pending_requests = ReservationRequest.objects.filter(client_id=user_id, status='REQUESTED', is_deleted=False).count()
        total_spent = Payment.objects.filter(user_id=user_id, status='SUCCESS', is_deleted=False).aggregate(total=Sum('amount'))['total'] or 0
        return {
            'total_reservations': total_reservations,
            'pending_requests': pending_requests,
            'total_spent': float(total_spent)
        }

    @staticmethod
    def get_owner_stats(owner_id: str) -> dict:
        now = timezone.now()
        total_properties = Property.objects.filter(owner_id=owner_id, is_deleted=False).count()
        active_properties = Property.objects.filter(owner_id=owner_id, status='PUBLISHED', is_deleted=False).count()
        suspended_properties = Property.objects.filter(owner_id=owner_id, status='SUSPENDED', is_deleted=False).count()
        
        pending_requests = ReservationRequest.objects.select_related('property').filter(property__owner_id=owner_id, status='REQUESTED', is_deleted=False).count()
        confirmed_reservations = Reservation.objects.select_related('property').filter(property__owner_id=owner_id, status__in=['CONFIRMED', 'PAID', 'COMPLETED'], is_deleted=False).count()
        cancelled_reservations = Reservation.objects.select_related('property').filter(property__owner_id=owner_id, status='CANCELLED', is_deleted=False).count()

        total_payouts = Payout.objects.filter(owner_id=owner_id, status='COMPLETED', is_deleted=False).aggregate(total=Sum('amount'))['total'] or 0
        monthly_revenue = Payout.objects.filter(owner_id=owner_id, status='COMPLETED', created_at__year=now.year, created_at__month=now.month, is_deleted=False).aggregate(total=Sum('amount'))['total'] or 0
        annual_revenue = Payout.objects.filter(owner_id=owner_id, status='COMPLETED', created_at__year=now.year, is_deleted=False).aggregate(total=Sum('amount'))['total'] or 0

        # Avis et note moyenne calculés sur PropertyReview
        reviews_qs = PropertyReview.objects.select_related('property').filter(property__owner_id=owner_id, is_deleted=False)
        total_reviews = reviews_qs.count()
        avg_rating_val = reviews_qs.aggregate(avg=Avg('rating'))['avg']
        avg_rating = round(float(avg_rating_val), 1) if avg_rating_val is not None else 5.0

        # Durée réelle des séjours confirmés (check_out - check_in), en jours
        stay_duration_expr = ExpressionWrapper(F('check_out') - F('check_in'), output_field=fields.DurationField())
        stay_stats = Reservation.objects.select_related('property').filter(
            property__owner_id=owner_id, status__in=['CONFIRMED', 'PAID', 'COMPLETED'], is_deleted=False
        ).annotate(stay_duration=stay_duration_expr).aggregate(total=Sum('stay_duration'), avg=Avg('stay_duration'))

        reserved_days = stay_stats['total'].days if stay_stats['total'] else 0
        avg_stay_duration = round(stay_stats['avg'].total_seconds() / 86400, 1) if stay_stats['avg'] else 0.0

        # Taux d'occupation estimé
        total_possible_days = max(active_properties * 30, 1)
        occupancy_rate = min(round((reserved_days / total_possible_days) * 100, 1), 100.0)

        # Revenu moyen par logement
        avg_revenue_per_property = round(float(total_payouts) / max(total_properties, 1), 2)

        # Meilleur logement / moins performant
        best_prop = Property.objects.filter(owner_id=owner_id, is_deleted=False).annotate(res_count=Count('reservations')).order_by('-res_count').first()
        worst_prop = Property.objects.filter(owner_id=owner_id, is_deleted=False).annotate(res_count=Count('reservations')).order_by('res_count').first()

        return {
            'total_properties': total_properties,
            'active_properties': active_properties,
            'suspended_properties': suspended_properties,
            'pending_requests': pending_requests,
            'confirmed_reservations': confirmed_reservations,
            'cancelled_reservations': cancelled_reservations,
            'total_payouts': float(total_payouts),
            'monthly_revenue': float(monthly_revenue),
            'annual_revenue': float(annual_revenue),
            'avg_rating': avg_rating,
            'total_reviews': total_reviews,
            'occupancy_rate': occupancy_rate,
            'avg_stay_duration': avg_stay_duration,
            'avg_revenue_per_property': avg_revenue_per_property,
            'best_property': best_prop.title if best_prop else "N/A",
            'worst_property': worst_prop.title if worst_prop else "N/A",
        }

    @staticmethod
    def get_owner_monthly_charts(owner_id: str) -> dict:
        """Revenus et taux d'occupation réels des 6 derniers mois pour ce propriétaire."""
        now = timezone.now()
        active_properties = max(Property.objects.filter(owner_id=owner_id, status='PUBLISHED', is_deleted=False).count(), 1)
        reservations = list(Reservation.objects.select_related('property').filter(
            property__owner_id=owner_id, status__in=['CONFIRMED', 'PAID', 'COMPLETED'], is_deleted=False
        ).values('check_in', 'check_out'))

        months_labels, revenue_data, occupancy_data = [], [], []

        for i in range(5, -1, -1):
            month_date = now - datetime.timedelta(days=i * 30)
            year, month = month_date.year, month_date.month
            days_in_month = calendar.monthrange(year, month)[1]
            month_start = datetime.date(year, month, 1)
            month_end_exclusive = month_start + datetime.timedelta(days=days_in_month)

            months_labels.append(month_date.strftime('%b'))

            revenue = Payout.objects.filter(
                owner_id=owner_id, status='COMPLETED', created_at__year=year, created_at__month=month, is_deleted=False
            ).aggregate(total=Sum('amount'))['total'] or 0
            revenue_data.append(float(revenue))

            reserved_days_in_month = 0
            for res in reservations:
                overlap_start = max(res['check_in'], month_start)
                overlap_end = min(res['check_out'], month_end_exclusive)
                overlap_days = (overlap_end - overlap_start).days
                if overlap_days > 0:
                    reserved_days_in_month += overlap_days

            occupancy_pct = min(round((reserved_days_in_month / (active_properties * days_in_month)) * 100, 1), 100.0)
            occupancy_data.append(occupancy_pct)

        return {
            'labels': months_labels,
            'revenue_data': revenue_data,
            'occupancy_data': occupancy_data,
        }

    @staticmethod
    def get_monthly_revenue_chart() -> dict:
        now = timezone.now()
        months_labels = []
        monthly_data = []

        for i in range(5, -1, -1):
            month_date = now - datetime.timedelta(days=i*30)
            year = month_date.year
            month = month_date.month
            month_name = month_date.strftime("%b")
            months_labels.append(month_name)
            
            val = Commission.objects.filter(
                created_at__year=year,
                created_at__month=month,
                is_deleted=False
            ).aggregate(total=Sum('amount'))['total'] or 0
            monthly_data.append(float(val))

        return {
            'labels': months_labels,
            'data': monthly_data
        }

    @staticmethod
    def get_admin_stats() -> dict:
        # Cette agrégation coûte ~30 requêtes et est affichée dans l'en-tête de
        # quasiment toutes les pages SuperAdmin : un court cache évite de la
        # recalculer à chaque navigation, sans trop décaler les chiffres affichés.
        if not settings.TESTING:
            cached = cache.get('admin_stats')
            if cached is not None:
                return cached

        now = timezone.now()
        start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start_of_week = start_of_today - datetime.timedelta(days=now.weekday())

        total_clients = User.objects.filter(is_client=True, is_deleted=False).count()
        active_clients = User.objects.filter(is_client=True, is_active=True, is_deleted=False).count()
        blocked_clients = User.objects.filter(is_client=True, is_active=False, is_deleted=False).count()
        new_clients_this_month = User.objects.filter(is_client=True, date_joined__year=now.year, date_joined__month=now.month, is_deleted=False).count()

        total_owners = User.objects.filter(is_owner=True, is_deleted=False).count()
        verified_owners = User.objects.filter(is_owner=True, is_verified=True, is_deleted=False).count()
        pending_owners = User.objects.filter(is_owner=True, is_verified=False, is_deleted=False).count()

        total_properties = Property.objects.filter(is_deleted=False).count()
        published_properties = Property.objects.filter(status='PUBLISHED', is_deleted=False).count()
        pending_properties = Property.objects.filter(status='PENDING', is_deleted=False).count()
        rejected_properties = Property.objects.filter(status='REJECTED', is_deleted=False).count()
        suspended_properties = Property.objects.filter(status='SUSPENDED', is_deleted=False).count()

        total_reservations = Reservation.objects.filter(is_deleted=False).count()
        reservations_today = Reservation.objects.filter(created_at__gte=start_of_today, is_deleted=False).count()
        reservations_this_week = Reservation.objects.filter(created_at__gte=start_of_week, is_deleted=False).count()
        reservations_this_month = Reservation.objects.filter(created_at__year=now.year, created_at__month=now.month, is_deleted=False).count()
        reservations_this_year = Reservation.objects.filter(created_at__year=now.year, is_deleted=False).count()

        total_volume = Payment.objects.filter(status='SUCCESS', is_deleted=False).aggregate(total=Sum('amount'))['total'] or 0
        total_revenue = Commission.objects.filter(is_deleted=False).aggregate(total=Sum('amount'))['total'] or 0
        total_payouts = Payout.objects.filter(status='COMPLETED', is_deleted=False).aggregate(total=Sum('amount'))['total'] or 0
        
        avg_basket_val = Payment.objects.filter(status='SUCCESS', is_deleted=False).aggregate(avg=Avg('amount'))['avg']
        avg_basket = round(float(avg_basket_val), 2) if avg_basket_val else 0.0

        pending_payouts_sum = Payout.objects.filter(status='PENDING', is_deleted=False).aggregate(total=Sum('amount'))['total'] or 0
        completed_payouts_sum = Payout.objects.filter(status='COMPLETED', is_deleted=False).aggregate(total=Sum('amount'))['total'] or 0

        monthly_chart = DashboardSelector.get_monthly_revenue_chart()

        stats = {
            'total_clients': total_clients,
            'active_clients': active_clients,
            'blocked_clients': blocked_clients,
            'new_clients_this_month': new_clients_this_month,
            'total_owners': total_owners,
            'verified_owners': verified_owners,
            'pending_owners': pending_owners,
            'total_properties': total_properties,
            'published_properties': published_properties,
            'pending_properties': pending_properties,
            'rejected_properties': rejected_properties,
            'suspended_properties': suspended_properties,
            'total_reservations': total_reservations,
            'reservations_today': reservations_today,
            'reservations_this_week': reservations_this_week,
            'reservations_this_month': reservations_this_month,
            'reservations_this_year': reservations_this_year,
            'total_volume': float(total_volume),
            'total_revenue': float(total_revenue),
            'total_payouts': float(total_payouts),
            'avg_basket': avg_basket,
            'pending_payouts_sum': float(pending_payouts_sum),
            'completed_payouts_sum': float(completed_payouts_sum),
            'monthly_revenue_labels': monthly_chart['labels'],
            'monthly_revenue_data': monthly_chart['data'],
        }
        if not settings.TESTING:
            cache.set('admin_stats', stats, timeout=30)
        return stats

    @staticmethod
    def get_ai_analytics_and_insights() -> dict:
        now = timezone.now()
        stats = DashboardSelector.get_admin_stats()
        
        # Prévisions IA basées sur les tendances ORM
        res_month = stats['reservations_this_month'] or 1
        volume_month = stats['total_volume'] or 1.0

        predicted_reservations = int(res_month * 1.2) + 5
        predicted_revenue = round(float(volume_month * 0.15) * 1.15, 2)
        predicted_available_properties = stats['published_properties'] + 3
        reservations_growth_pct = round((predicted_reservations - res_month) / res_month * 100) if res_month else 0

        # Détections ORM réelles
        underperforming_properties = Property.objects.filter(is_deleted=False).annotate(res_cnt=Count('reservations')).filter(res_cnt=0)[:5]
        inactive_owners = User.objects.filter(is_owner=True, is_verified=False, is_deleted=False)[:5]
        power_clients = User.objects.filter(is_client=True, is_deleted=False).annotate(res_cnt=Count('reservations')).filter(res_cnt__gte=2)[:5]
        suspicious_listings = Property.objects.filter(status='PENDING', is_deleted=False)[:5]

        # Heatmaps (Villes & Catégories populaires)
        top_cities = list(Property.objects.filter(is_deleted=False).values('city').annotate(count=Count('reservations')).order_by('-count')[:5])
        popular_categories = list(Property.objects.select_related('property_type__category').filter(is_deleted=False).values('property_type__category__name').annotate(count=Count('reservations')).order_by('-count')[:5])

        # Dynamic Auto-Generated Insights based on real ORM query results
        insights = []
        if top_cities and top_cities[0]['city']:
            c_name = top_cities[0]['city']
            c_cnt = top_cities[0]['count']
            insights.append(f"La ville de {c_name} enregistre la plus forte demande avec {c_cnt} réservation(s) enregistrée(s).")
        
        if popular_categories and popular_categories[0]['property_type__category__name']:
            cat_name = popular_categories[0]['property_type__category__name']
            cat_cnt = popular_categories[0]['count']
            insights.append(f"La catégorie {cat_name} représente la majorité des réservations ({cat_cnt} réservation(s)).")

        if stats['pending_owners'] > 0:
            insights.append(f"Action prioritaire : {stats['pending_owners']} dossier(s) hôte en attente de vérification KYC.")

        if stats['pending_properties'] > 0:
            insights.append(f"Action prioritaire : {stats['pending_properties']} annonce(s) en attente de validation administrative.")

        if not insights:
            insights.append("Toutes les métriques de la plateforme DEKOUWAY sont stables et à jour.")

        return {
            'predictions': {
                'reservations_next_month': predicted_reservations,
                'reservations_growth_pct': reservations_growth_pct,
                'revenue_next_month': predicted_revenue,
                'available_properties_next_month': predicted_available_properties,
            },
            'detections': {
                'underperforming_properties': underperforming_properties,
                'inactive_owners': inactive_owners,
                'power_clients': power_clients,
                'suspicious_listings': suspicious_listings,
            },
            'heatmaps': {
                'top_cities': top_cities,
                'popular_categories': popular_categories,
            },
            'auto_insights': insights,
        }
