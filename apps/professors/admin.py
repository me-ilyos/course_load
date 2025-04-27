from django.contrib import admin
from .models import Professor


@admin.register(Professor)
class ProfessorAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'title', 'employee_id', 'department', 'employment_type', 'is_degree_holder', 'is_department_head')
    list_filter = ('department', 'title', 'employment_type', 'is_degree_holder')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'employee_id')
    ordering = ('user__last_name', 'user__first_name')
    raw_id_fields = ('user',)
    
    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    get_full_name.short_description = 'Name'
    
    def is_department_head(self, obj):
        return obj.user.is_department_head()
    is_department_head.boolean = True
    is_department_head.short_description = 'Department Head'
    
    def get_queryset(self, request):
        """Optimize queries by prefetching related fields"""
        return super().get_queryset(request).select_related('user', 'department')
