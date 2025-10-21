from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('quiz/', views.quiz_view, name='quiz'),
    path('daily-entry/', views.daily_entry_view, name='daily_entry'),
    path('entries-history/', views.entries_history_view, name='entries_history'),
    path('reveal-advice/', views.reveal_advice_view, name='reveal_advice'),
    path('tasks/', views.tasks_view, name='tasks'),
    path('tasks/<int:task_id>/start/', views.start_task_view, name='start_task'),
    path('tasks/<int:task_id>/complete/', views.complete_task_view, name='complete_task'),
    path('tarot/', views.tarot_view, name='tarot'),
    path('natal-chart/', views.natal_chart_view, name='natal_chart'),
    path('statistics/', views.statistics_view, name='statistics'),
]
