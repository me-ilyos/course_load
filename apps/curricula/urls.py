from django.urls import path
from .views import parse_curriculum_excel

urlpatterns = [
    path('parse-excel/', parse_curriculum_excel, name='parse_curriculum_excel'),
] 