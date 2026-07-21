from django.urls import path
from . import views

urlpatterns = [
    path('', views.SupportHomeView.as_view(), name='support'),
    path('widget/', views.ChatbotWidgetView.as_view(), name='chatbot_widget'),
    path('chat/', views.ChatbotResponseView.as_view(), name='chatbot_response'),
]
