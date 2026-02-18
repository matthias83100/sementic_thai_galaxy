import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from vocab_app.models import UserWordInfo, Word
from vocab_app.serializers import UserWordInfoSerializer

class Command(BaseCommand):
    help = 'Exports a subset of UserWordInfo to a static JSON for guests.'

    def handle(self, *args, **options):
        # We need to pick a user's collection to export. 
        # For a "seed" file, we can either take calculations from a specific admin user 
        # or just take the first 100 UserWordInfo objects if they are representative.
        # Alternatively, if we want high quality, we might want to run UMAP on the first 100 Words.
        
        # Let's take the first UserWordInfo objects found in the DB (assuming they are already optimized)
        # Or better: Pick the most populated user's collection.
        
        target_user_info = UserWordInfo.objects.all().select_related('word')[:100]
        
        if not target_user_info:
            self.stdout.write(self.style.WARNING("No UserWordInfo found in database. Exporting empty list."))
            data = []
        else:
            serializer = UserWordInfoSerializer(target_user_info, many=True)
            data = serializer.data

        output_dir = os.path.join(settings.BASE_DIR, 'vocab_app', 'static', 'vocab_app', 'data')
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, 'guest_galaxy.json')

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        self.stdout.write(self.style.SUCCESS(f'Successfully exported {len(data)} words to {output_path}'))
