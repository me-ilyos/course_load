from django.db import models
from django.conf import settings


class Department(models.Model):
    """
    Department model representing an academic department within the institution.
    """
    title = models.CharField(max_length=100, help_text="Department name")
    code = models.CharField(max_length=10, unique=True, help_text="Department code (e.g., CS, ENG)")
    department_head = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='headed_department',
        limit_choices_to={'user_type': 'department_head'},
        help_text="Professor who is the head of this department"
    )
    # Calculated fields for total assigned hours
    total_lecture_hours = models.PositiveIntegerField(default=0, editable=False, help_text="Total lecture hours assigned from all curricula")
    total_practice_hours = models.PositiveIntegerField(default=0, editable=False, help_text="Total practice hours assigned from all curricula")
    total_laboratory_hours = models.PositiveIntegerField(default=0, editable=False, help_text="Total laboratory hours assigned from all curricula")
    total_seminar_hours = models.PositiveIntegerField(default=0, editable=False, help_text="Total seminar hours assigned from all curricula")
    
    def __str__(self):
        return f"{self.code} - {self.title}"
    
    class Meta:
        ordering = ['code']
        verbose_name = "Department"
        verbose_name_plural = "Departments"
        
    def save(self, *args, **kwargs):
        # Make sure the code is uppercase
        self.code = self.code.upper()
        super().save(*args, **kwargs)
        
        # If department head is assigned, update their user type to department_head
        if self.department_head and self.department_head.user_type != 'department_head':
            from apps.core.models import User
            self.department_head.user_type = User.DEPARTMENT_HEAD
            self.department_head.save(update_fields=['user_type'])
