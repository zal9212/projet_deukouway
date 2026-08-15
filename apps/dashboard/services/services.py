from apps.accounts.models import User
from apps.dashboard.services.selectors import DashboardSelector
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class DashboardService:

    @staticmethod
    def get_client_dashboard(client: User) -> dict:
        """Agrège les données pour le tableau de bord du client."""
        logger.info(f"Génération du tableau de bord client pour {client.email}")
        return {
            "recent_activity": DashboardSelector.get_recent_activity(client.id),
            "total_bookings": DashboardService.calculate_bookings(client),
            # Ajouter d'autres agrégations ici
        }

    @staticmethod
    def get_owner_dashboard(owner: User) -> dict:
        """Agrège les données pour le tableau de bord du propriétaire."""
        logger.info(f"Génération du tableau de bord propriétaire pour {owner.email}")
        return {
            "recent_activity": DashboardSelector.get_recent_activity(owner.id),
            "total_revenue": DashboardService.calculate_revenue(owner),
            "total_bookings": DashboardService.calculate_bookings(owner, as_owner=True)
        }

    @staticmethod
    def get_admin_dashboard(admin: User) -> dict:
        """Agrège les données pour le tableau de bord SuperAdmin."""
        logger.info(f"Génération du tableau de bord admin pour {admin.email}")
        return {
            "system_logs": DashboardSelector.get_system_logs(),
            "platform_revenue": DashboardService.calculate_revenue(admin, global_revenue=True),
            "platform_growth": DashboardService.calculate_growth()
        }

    @staticmethod
    def calculate_statistics() -> dict:
        """Calcule les statistiques globales pour DEKOUWAY."""
        return {
            "total_users": User.objects.count(),
            # Ajouter des agrégations complexes ici
        }

    @staticmethod
    def calculate_revenue(user: User, global_revenue: bool = False) -> Decimal:
        """Calcule les revenus. Si global_revenue est True, calcule la commission totale de DEKOUWAY."""
        if global_revenue:
            # Requête de la somme globale des commissions
            return Decimal('0.00')
        else:
            # Requête de la somme des reversements pour ce propriétaire
            return Decimal('0.00')

    @staticmethod
    def calculate_bookings(user: User, as_owner: bool = False) -> int:
        """Calcule le nombre de réservations."""
        if as_owner:
            return 0 # Compte les réservations des propriétés du propriétaire
        return 0 # Compte les réservations du client

    @staticmethod
    def calculate_growth() -> dict:
        """Calcule les indicateurs de croissance mensuelle."""
        return {
            "users_growth": "+5%",
            "revenue_growth": "+12%"
        }
