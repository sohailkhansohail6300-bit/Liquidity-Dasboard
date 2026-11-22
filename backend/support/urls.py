from django.urls import path

from core import views

urlpatterns = [
    path('tickets/', views.TicketListView.as_view()),
    path('tickets/<str:ticket_id>/', views.TicketDetailView.as_view()),
    path('tickets/<str:ticket_id>/messages/', views.TicketMessageView.as_view()),
    path('tickets/<str:ticket_id>/status/', views.TicketStatusView.as_view()),
]
