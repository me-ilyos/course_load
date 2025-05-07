from django.urls import path
from .views import upload_excel, CurriculumListView, curriculum_create_view

app_name = 'curricula'

urlpatterns = [
    path('upload/', upload_excel, name='upload_excel'),
    path('', CurriculumListView.as_view(), name='curriculum_list'),
    path('create/', curriculum_create_view, name='curriculum_create'),
] 