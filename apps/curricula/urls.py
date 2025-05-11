from django.urls import path
from .views import (
    upload_excel, 
    CurriculumListView, 
    curriculum_create_view, 
    CurriculumDetailView,
    update_course_data_view
)

app_name = 'curricula'

urlpatterns = [
    path('upload/', upload_excel, name='upload_excel'),
    path('', CurriculumListView.as_view(), name='curriculum_list'),
    path('create/', curriculum_create_view, name='curriculum_create'),
    path('<int:pk>/', CurriculumDetailView.as_view(), name='curriculum_detail'),
    path('<int:pk>/update_course/', update_course_data_view, name='update_course_data'),
] 