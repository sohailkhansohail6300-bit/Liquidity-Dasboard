from django.urls import path

from . import views

urlpatterns = [
    path('meta/', views.MetaView.as_view()),
    path('demo/samples/', views.DemoSamplesView.as_view()),
    path('auth/csrf/', views.CsrfView.as_view()),
    path('auth/login/', views.LoginView.as_view()),
    path('auth/logout/', views.LogoutView.as_view()),
    path('auth/me/', views.MeView.as_view()),
    path('auth/account/', views.AccountView.as_view()),
    path('auth/password/change/', views.PasswordChangeView.as_view()),
    path('auth/password/reset/', views.PasswordResetView.as_view()),
    path('auth/password/reset/confirm/', views.PasswordResetConfirmView.as_view()),
    path('signup/<str:token>/', views.SignupLinkView.as_view()),
    path('access-requests/', views.AccessRequestView.as_view()),
]
