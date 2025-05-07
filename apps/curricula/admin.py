from django.contrib import admin
from .models import Curriculum

@admin.register(Curriculum)
class CurriculumAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'start_year', 'degree', 'duration')
    list_filter = ('degree', 'start_year')
    search_fields = ('code', 'title')
