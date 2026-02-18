import json
import os
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.conf import settings
from .models import Word, UserWordInfo

@receiver(post_save, sender=User)
def create_guest_collection(sender, instance, created, **kwargs):
    if created:
        json_path = os.path.join(settings.BASE_DIR, 'vocab_app', 'static', 'vocab_app', 'data', 'guest_galaxy.json')
        if not os.path.exists(json_path):
            return

        with open(json_path, 'r', encoding='utf-8') as f:
            guest_words = json.load(f)

        user_infos = []
        for item in guest_words:
            word_data = item['word']
            # Get or create the base word
            word, _ = Word.objects.get_or_create(
                thai=word_data['thai'],
                defaults={'french': word_data['french']}
            )
            
            # Create UserWordInfo preserving coordinates but RESETTING progress
            user_infos.append(UserWordInfo(
                user=instance,
                word=word,
                x=item['x'],
                y=item['y'],
                z=item['z'],
                cluster_id=item['cluster_id'],
                cluster_label=item['cluster_label'],
                flashcard_infos=item['flashcard_infos'],
                is_favorite=False,  # Reset
                srs_level=0,       # Reset to fresh start
                next_review_date=None,
                last_review_date=None,
                tags=item.get('tags', [])
            ))


        UserWordInfo.objects.bulk_create(user_infos, ignore_conflicts=True)
