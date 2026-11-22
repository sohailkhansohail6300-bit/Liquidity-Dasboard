from django.urls import path

from core import views

urlpatterns = [
    path('companies/', views.CompanyListView.as_view()),
    path('companies/<str:company_id>/kpi/', views.KpiView.as_view()),
    path('companies/<str:company_id>/team/', views.TeamView.as_view()),
    path('companies/<str:company_id>/profile-reviews/', views.ProfileReviewView.as_view()),
    path('companies/<str:company_id>/profile-reviews/pending/', views.PendingProfileReviewView.as_view()),
    path('companies/<str:company_id>/trades/', views.TradeView.as_view()),
    path('companies/<str:company_id>/statements/', views.StatementView.as_view()),
]
