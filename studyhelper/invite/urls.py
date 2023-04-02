from django.urls import path
from . import views

app_name = 'invite'

urlpatterns = [
    path('', views.home, name='home'),
    path('sessions', views.user_home, name='user_home'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('anonymous-session-result/<int:session_score_id>/', views.session_result, name='session_result'),
    path('anonymous-user-results/<int:user_id>/', views.user_results, name='list_user_results'),
]
