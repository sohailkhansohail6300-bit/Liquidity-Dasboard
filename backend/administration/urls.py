from django.urls import path

from core import views

urlpatterns = [
    path('admin/counts/', views.AdminCountsView.as_view()),
    path('admin/users/', views.AdminUsersView.as_view()),
    path('admin/users/<int:person_id>/access/', views.AdminUserAccessView.as_view()),
    path('admin/users/<int:person_id>/', views.AdminUserAccessView.as_view()),
    path('admin/users/admins/', views.AdminAddAdminView.as_view()),
    path('admin/signup-links/', views.AdminSignupLinksView.as_view()),
    path('admin/signup-links/<str:link_id>/revoke/', views.AdminSignupLinkRevokeView.as_view()),
    path('admin/access-requests/', views.AdminAccessRequestsView.as_view()),
    path('admin/access-requests/<str:request_id>/decision/', views.AdminAccessRequestDecisionView.as_view()),
    path('admin/profile-reviews/', views.AdminProfileReviewsView.as_view()),
    path('admin/profile-reviews/<str:review_id>/decision/', views.AdminProfileReviewDecisionView.as_view()),
    path('admin/subscriptions/<str:company_id>/', views.AdminSubscriptionView.as_view()),
    path('admin/feeds/', views.AdminFeedsView.as_view()),
    path('admin/access-log/', views.AdminAccessLogView.as_view()),
]
