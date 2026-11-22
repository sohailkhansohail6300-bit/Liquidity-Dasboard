from django.urls import path

from core import views

urlpatterns = [
    path('subscriptions/', views.SubscriptionView.as_view()),
]
