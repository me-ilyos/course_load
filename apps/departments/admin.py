from django.contrib import admin
from .models import Department


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'department_head')
    list_filter = ('code',)
    search_fields = ('code', 'title', 'department_head__username', 'department_head__first_name', 'department_head__last_name')
    ordering = ('code',)
    
    def get_queryset(self, request):
        """Optimize queries by prefetching department_head"""
        return super().get_queryset(request).select_related('department_head')
