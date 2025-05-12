from django.urls import path
from . import views

app_name = 'professors'

urlpatterns = [
    path('', views.ProfessorListView.as_view(), name='professor_list'),
    path('<int:pk>/edit/', views.ProfessorUpdateView.as_view(), name='professor_edit'),
    path('<int:pk>/delete/', views.ProfessorDeleteView.as_view(), name='professor_delete'),
] 