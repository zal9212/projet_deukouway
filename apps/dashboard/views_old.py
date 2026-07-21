from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Sum, Count
from django.contrib import messages
from properties.models import Property
from bookings.models import Booking
from django.contrib.auth import get_user_model

User = get_user_model()

class OwnerDashboardView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Dashboard for owners showing property statistics, listings, and booking requests.
    """
    def test_func(self):
        return self.request.user.role == 'owner'

    def get(self, request):
        owner = request.user
        properties = Property.objects.filter(owner=owner)
        bookings = Booking.objects.filter(property__owner=owner).select_related('property', 'client')
        
        # Financial & Booking stats
        total_revenue = bookings.filter(status='confirmed').aggregate(Sum('total_price'))['total_price__sum'] or 0
        total_properties = properties.count()
        total_bookings = bookings.count()
        pending_bookings = bookings.filter(status='pending')
        
        # Occupation Rate calculation
        occupied_properties = bookings.filter(status='confirmed').values('property').distinct().count()
        occupation_rate = int((occupied_properties / total_properties) * 100) if total_properties > 0 else 0

        context = {
            'properties': properties,
            'bookings': bookings,
            'pending_bookings': pending_bookings,
            'total_revenue': total_revenue,
            'total_properties': total_properties,
            'total_bookings': total_bookings,
            'occupation_rate': occupation_rate
        }
        return render(request, 'pages/owner/dashboard.html', context)


class OwnerPropertiesView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    List of listings owned by the authenticated owner.
    """
    def test_func(self):
        return self.request.user.role == 'owner'

    def get(self, request):
        properties = Property.objects.filter(owner=self.request.user)
        return render(request, 'pages/owner/properties.html', {'properties': properties})


class OwnerBookingsView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    List of reservations received for properties owned by the authenticated owner.
    """
    def test_func(self):
        return self.request.user.role == 'owner'

    def get(self, request):
        bookings = Booking.objects.filter(property__owner=self.request.user).select_related('property', 'client')
        return render(request, 'pages/owner/bookings.html', {'bookings': bookings})


class AdminDashboardView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    System moderation panel for Admins (owners validation & properties moderation).
    """
    def test_func(self):
        return self.request.user.role == 'admin' or self.request.user.is_superuser

    def get(self, request):
        # Overall metrics
        total_users = User.objects.count()
        total_properties = Property.objects.count()
        total_bookings = Booking.objects.count()
        
        # Moderation lists
        pending_owners = User.objects.filter(role='owner', owner_status='pending')
        pending_properties = Property.objects.filter(status='pending').select_related('owner')

        context = {
            'total_users': total_users,
            'total_properties': total_properties,
            'total_bookings': total_bookings,
            'pending_owners': pending_owners,
            'pending_properties': pending_properties
        }
        return render(request, 'pages/admin/dashboard.html', context)


class AdminValidationView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Lists accounts and properties waiting for validation.
    """
    def test_func(self):
        return self.request.user.role == 'admin' or self.request.user.is_superuser

    def get(self, request):
        pending_owners = User.objects.filter(role='owner', owner_status='pending')
        pending_properties = Property.objects.filter(status='pending').select_related('owner')
        context = {
            'pending_owners': pending_owners,
            'pending_properties': pending_properties
        }
        return render(request, 'pages/admin/validation.html', context)


class AdminPropertiesView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Lists all properties in the system for admin search/moderation.
    """
    def test_func(self):
        return self.request.user.role == 'admin' or self.request.user.is_superuser

    def get(self, request):
        properties = Property.objects.all().select_related('owner')
        return render(request, 'pages/admin/properties.html', {'properties': properties})


class AdminUsersView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Lists all users registered in the system.
    """
    def test_func(self):
        return self.request.user.role == 'admin' or self.request.user.is_superuser

    def get(self, request):
        members = User.objects.all()
        return render(request, 'pages/admin/users.html', {'members': members})


class AdminStatisticsView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Displays system reports.
    """
    def test_func(self):
        return self.request.user.role == 'admin' or self.request.user.is_superuser

    def get(self, request):
        return render(request, 'pages/admin/statistics.html')


class ModerationActionView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Moderation execution triggers (Approve Owner, Reject Owner, Publish Property, Reject Property).
    """
    def test_func(self):
        return self.request.user.role == 'admin' or self.request.user.is_superuser

    def post(self, request):
        target_type = request.POST.get('target_type')
        target_id = request.POST.get('target_id')
        action = request.POST.get('action')

        if target_type == 'owner':
            owner = get_object_or_404(User, id=target_id, role='owner')
            if action == 'approve':
                owner.owner_status = 'approved'
                owner.is_verified_owner = True
                owner.save()
                messages.success(request, f"Le compte propriétaire de {owner.get_full_name()} a été approuvé.")
            elif action == 'reject':
                owner.owner_status = 'rejected'
                owner.is_verified_owner = False
                owner.save()
                messages.warning(request, f"Le compte propriétaire de {owner.get_full_name()} a été rejeté.")
                
        elif target_type == 'property':
            property_obj = get_object_or_404(Property, id=target_id)
            if action == 'approve':
                property_obj.status = 'approved'
                property_obj.save()
                messages.success(request, f"L'annonce '{property_obj.title}' a été validée et publiée.")
            elif action == 'reject':
                property_obj.status = 'rejected'
                property_obj.save()
                messages.warning(request, f"L'annonce '{property_obj.title}' a été rejetée.")

        return redirect('admin_dashboard')
