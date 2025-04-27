from django.db import models
from django.conf import settings


class Professor(models.Model):
    """
    Professor model extending the User model with additional professor-specific fields.
    """
    EMPLOYMENT_CHOICES = [
        (0.25, '0.25'),
        (0.50, '0.50'),
        (0.75, '0.75'),
        (1.00, '1.00'),
        (1.25, '1.25'),
        (1.50, '1.50'),
        (1.75, '1.75'),
        (2.00, '2.00'),
    ]
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='professor_profile',
        limit_choices_to={'user_type__in': ['professor', 'department_head']},
    )
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='professors'
    )
    employee_id = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=50, help_text="Academic title (e.g., Assistant Professor)")
    employment_type = models.FloatField(
        choices=EMPLOYMENT_CHOICES,
        default=1.0,
        help_text="Employment type (fraction of full-time)"
    )
    is_degree_holder = models.BooleanField(
        default=False,
        help_text="Whether the professor holds a doctoral degree"
    )
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} ({self.title})"
    
    class Meta:
        ordering = ['user__last_name', 'user__first_name']
        verbose_name = "Professor"
        verbose_name_plural = "Professors"
