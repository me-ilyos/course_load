from django.db import models

# Create your models here.

class Curriculum(models.Model):
    DEGREE_CHOICES = [
        ('Bachelors', 'Bachelors'),
        ('Masters', 'Masters'),
    ]

    code = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=255)
    start_year = models.PositiveIntegerField()
    degree = models.CharField(max_length=20, choices=DEGREE_CHOICES)
    duration = models.PositiveIntegerField()
    data = models.JSONField(null=True, blank=True, help_text="JSON data about mandatory and selective courses")

    @property
    def academic_year_display(self):
        if self.start_year:
            return f"{self.start_year}/{self.start_year + 1}"
        return ""

    def __str__(self):
        return f"{self.title} ({self.code}) - {self.start_year}"

    class Meta:
        verbose_name = "Curriculum"
        verbose_name_plural = "Curricula"
        ordering = ['title', 'start_year']
