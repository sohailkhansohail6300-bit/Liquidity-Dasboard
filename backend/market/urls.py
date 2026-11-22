from django.urls import path

from core import views

urlpatterns = [
    path('peer-groups/', views.PeerGroupView.as_view()),
    path('reports/', views.ReportView.as_view()),
]
