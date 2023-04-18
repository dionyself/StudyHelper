from django.urls import path
from . import views

app_name = 'quiz'

urlpatterns = [
    path('', views.home, name='home'),
    path('user-home', views.user_home, name='user_home'),
    path('play/', views.play, name='play'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('reset/', views.reset, name='reset'),
    path('submission-result/<int:attempted_question_pk>/', views.submission_result, name='submission_result'),
    path('session-result/<int:session_score_id>/', views.session_result, name='session_result'),
    path('user-results/<int:user_id>/', views.user_results, name='list_user_results'),
    path('as-template/<int:session_id>/', views.as_template, name='use_session_as_template'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('import_export/', views.import_export, name='import_export'),

]
