from django.contrib import admin
from .models import Word, UserWordInfo, QuizResult

@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    list_display = ('thai', 'french')
    search_fields = ('thai', 'french')

@admin.register(UserWordInfo)
class UserWordInfoAdmin(admin.ModelAdmin):
    list_display = ('user', 'word_thai', 'word_french', 'srs_level', 'next_review_date', 'last_review_date', 'add_date', 'is_favorite')
    list_filter = ('user', 'is_favorite', 'srs_level', 'cluster_label', 'add_date', 'last_review_date')
    search_fields = ('word__thai', 'word__french', 'user__username', 'cluster_label')
    date_hierarchy = 'add_date'
    ordering = ('-add_date',)

    def word_thai(self, obj):
        return obj.word.thai
    word_thai.short_description = 'Thai'
    word_thai.admin_order_field = 'word__thai'

    def word_french(self, obj):
        return obj.word.french
    word_french.short_description = 'French'
    word_french.admin_order_field = 'word__french'

@admin.register(QuizResult)
class QuizResultAdmin(admin.ModelAdmin):
    list_display = ('user', 'word_thai', 'quiz_type', 'result', 'review_date')
    list_filter = ('user', 'quiz_type', 'result', 'review_date')
    search_fields = ('word__thai', 'word__french', 'user__username')
    date_hierarchy = 'review_date'
    
    def word_thai(self, obj):
        return obj.word.thai
    word_thai.short_description = 'Word'
    word_thai.admin_order_field = 'word__thai'
