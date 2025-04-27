from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/admin/', views.academic_admin_dashboard, name='academic_admin_dashboard'),
    path('dashboard/department-head/', views.department_head_dashboard, name='department_head_dashboard'),
    path('dashboard/professor/', views.professor_dashboard, name='professor_dashboard'),
] 