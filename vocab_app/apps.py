from django.apps import AppConfig


class VocabAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'vocab_app'

    def ready(self):
        import os
        from . import signals  # Import signals
        
        # Only load in the main process (avoids double-load with runserver --reload)
        if os.environ.get('RUN_MAIN') == 'true':
            from . import services
            print("🔄 Pre-loading Thai models at startup...")
            services.get_thai_model()
            services.get_thai_word_set()
            print("✅ Thai models loaded!")

