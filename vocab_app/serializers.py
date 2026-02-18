from rest_framework import serializers
from .models import Word, UserWordInfo, QuizResult

class WordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Word
        fields = ['id', 'thai', 'french']

class UserWordInfoSerializer(serializers.ModelSerializer):
    word = WordSerializer(read_only=True)
    
    class Meta:
        model = UserWordInfo
        fields = ['id', 'word', 'x', 'y', 'z', 'cluster_id', 'cluster_label', 'flashcard_infos', 'is_favorite', 'srs_level', 'tags', 'add_date', 'last_review_date']

class QuizResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizResult
        fields = '__all__'
