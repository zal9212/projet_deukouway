from django.urls import path
from . import views

urlpatterns = [
    path('owner/', views.OwnerDashboardView.as_view(), name='owner_dashboard'),
    path('owner/properties/', views.OwnerPropertiesView.as_view(), name='owner_properties'),
    path('owner/bookings/', views.OwnerBookingsView.as_view(), name='owner_bookings'),
    
    path('admin/', views.AdminDashboardView.as_view(), name='admin_dashboard'),
    path('admin/validation/', views.AdminValidationView.as_view(), name='admin_validation'),
    path('admin/properties/', views.AdminPropertiesView.as_view(), name='admin_properties'),
    path('admin/users/', views.AdminUsersView.as_view(), name='admin_users'),
    path('admin/statistics/', views.AdminStatisticsView.as_view(), name='admin_statistics'),
    
    path('moderation/', views.ModerationActionView.as_view(), name='moderation_action'),
]
