from django.apps import AppConfig


class CurriculaConfig(AppConfig):
    """Configuration for the curricula app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.curricula'
    verbose_name = 'Curricula Management'

    def ready(self):
        """Initialize app when Django starts."""
        # Import signal handlers or perform other initialization
        pass
