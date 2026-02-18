from django.db import models
from django.contrib.auth.models import User
import json

class Word(models.Model):
    thai = models.CharField(max_length=255)
    french = models.CharField(max_length=255)
    vector = models.JSONField(default=list)

    def __str__(self):
        return self.thai

class UserWordInfo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    word = models.ForeignKey(Word, on_delete=models.CASCADE)

    # Coordinates
    x = models.FloatField(default=0.0)
    y = models.FloatField(default=0.0)
    z = models.FloatField(default=0.0)

    # Personal Clustering
    cluster_id = models.IntegerField(null=True, blank=True)
    cluster_label = models.CharField(max_length=255, null=True, blank=True)

    add_date = models.DateTimeField(auto_now_add=True)

    # Flashcard specific data
    flashcard_infos = models.JSONField(default=dict)

    is_favorite = models.BooleanField(default=False)

    # SRS Logic
    srs_level = models.IntegerField(default=0)
    next_review_date = models.DateTimeField(null=True, blank=True)
    last_review_date = models.DateTimeField(null=True, blank=True)

    tags = models.JSONField(default=list)

    class Meta:
        unique_together = ('user', 'word')

class QuizResult(models.Model):
    QUIZ_TYPES = [
        ('fr2th', 'French to Thai'),
        ('th2fr', 'Thai to French'),
        ('audio', 'Audio'),
        ('sentence', 'Sentence Completion'),
    ]

    RESULT_TYPES = [
        ('fail', 'False'),
        ('hard', 'Hard'),
        ('good', 'Good'),
        ('easy', 'Easy'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    word = models.ForeignKey(Word, on_delete=models.CASCADE)
    quiz_id = models.CharField(max_length=100)
    quiz_type = models.CharField(max_length=20, choices=QUIZ_TYPES)
    result = models.CharField(max_length=20, choices=RESULT_TYPES)
    review_date = models.DateTimeField(auto_now_add=True)
