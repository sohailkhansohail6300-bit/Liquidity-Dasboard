from django.urls import path

from core import views

urlpatterns = [
    path('team/invitations/', views.TeamInvitationView.as_view()),
    path('team/members/<int:person_id>/access/', views.TeamMemberAccessView.as_view()),
    path('team/members/<int:person_id>/', views.TeamMemberAccessView.as_view()),
]
