from django.core.management.base import BaseCommand
from vocab_app.models import UserWordInfo, QuizResult
from django.db.models import Max

class Command(BaseCommand):
    help = 'Backfills last_review_date from QuizResult history'

    def handle(self, *args, **options):
        self.stdout.write("Starting backfill of last_review_date...")
        
        # Optimize by using aggregation if possible, or iterating
        # Standard approach: Iterate words, find latest quiz result
        
        updated_count = 0
        user_words = UserWordInfo.objects.all()
        total = user_words.count()
        
        self.stdout.write(f"checking {total} user words...")

        batch = []
        for i, uwi in enumerate(user_words):
            latest_result = QuizResult.objects.filter(
                user=uwi.user, 
                word=uwi.word
            ).order_by('-review_date').first()
            
            if latest_result:
                uwi.last_review_date = latest_result.review_date
                batch.append(uwi)
                updated_count += 1
            
            if len(batch) >= 100:
                UserWordInfo.objects.bulk_update(batch, ['last_review_date'])
                batch = []
                self.stdout.write(f"Processed {i+1}/{total}...")

        if batch:
            UserWordInfo.objects.bulk_update(batch, ['last_review_date'])

        self.stdout.write(self.style.SUCCESS(f"Successfully backfilled {updated_count} words."))
