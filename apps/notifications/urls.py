from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('<uuid:pk>/', views.NotificationOpenView.as_view(), name='open'),
    path('tout-marquer-lu/', views.NotificationMarkAllReadView.as_view(), name='mark_all_read'),
]
