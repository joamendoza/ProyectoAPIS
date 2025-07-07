from django.apps import AppConfig


class FerremasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ferremas'
    
    def ready(self):
        """Initialize MongoDB when Django starts"""
        try:
            from .mongo_config import configure_mongoengine
            configure_mongoengine()
        except Exception as e:
            print(f"⚠️  Warning: Could not initialize MongoDB: {e}")
