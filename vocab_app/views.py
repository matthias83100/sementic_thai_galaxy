from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Word, UserWordInfo, QuizResult
from .serializers import UserWordInfoSerializer, QuizResultSerializer
from . import services
import numpy as np
from datetime import timedelta
import json

# SRS interval ladder (in minutes)
SRS_INTERVALS = [1, 10, 1440, 4320, 10080, 20160, 43200, 129600, 259200]

def get_srs_interval(level):
    """Return timedelta for a given SRS level."""
    idx = min(level, len(SRS_INTERVALS) - 1)
    return timedelta(minutes=SRS_INTERVALS[idx])


def index(request):
    context = {
        'is_guest': not request.user.is_authenticated
    }
    return render(request, 'vocab_app/index.html', context)


from .forms import SignUpForm, LoginForm

def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
    else:
        form = SignUpForm()
    return render(request, 'vocab_app/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('index')
    else:
        form = LoginForm()
    return render(request, 'vocab_app/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('index')



class MapDataView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        if request.user.is_authenticated:
            user_words = UserWordInfo.objects.filter(user=request.user).select_related('word')
            serializer = UserWordInfoSerializer(user_words, many=True)
            return Response(serializer.data)
        else:
            # Serve from static JSON for guests
            import json
            import os
            from django.conf import settings
            json_path = os.path.join(settings.BASE_DIR, 'vocab_app', 'static', 'vocab_app', 'data', 'guest_galaxy.json')
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    return Response(json.load(f))
            return Response([])


class PreviewWordView(APIView):
    """Generate flashcard info for review WITHOUT saving to DB."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        thai = request.data.get('thai')
        french = request.data.get('french')
        sentence = request.data.get('sentence', '')

        if not thai or not french:
            return Response({"error": "Thai and French words are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            flashcard_infos = services.get_flashcard_infos(thai, french, sentence)
        except Exception as e:
            print(f"Error generating flashcard info: {e}")
            flashcard_infos = {}

        return Response(flashcard_infos, status=status.HTTP_200_OK)


class AddWordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        thai = request.data.get('thai')
        french = request.data.get('french')
        sentence = request.data.get('sentence', '')

        if not thai or not french:
            return Response({"error": "Thai and French words are required."}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Get or Create Word
        word, created = Word.objects.get_or_create(thai=thai, defaults={'french': french})
        
        # 2. Check if user has it
        if UserWordInfo.objects.filter(user=request.user, word=word).exists():
            # Retrieve existing to return it
            existing = UserWordInfo.objects.get(user=request.user, word=word)
            return Response(UserWordInfoSerializer(existing).data, status=status.HTTP_200_OK)

        # 3. Use pre-reviewed flashcard_infos if provided, otherwise generate
        flashcard_infos = request.data.get('flashcard_infos')
        if not flashcard_infos:
            try:
                flashcard_infos = services.get_flashcard_infos(thai, french, sentence)
            except Exception as e:
                print(f"Error generating flashcard info: {e}")
                flashcard_infos = {}

        # 4. Create UserWordInfo
        user_word = UserWordInfo.objects.create(
            user=request.user,
            word=word,
            flashcard_infos=flashcard_infos
        )

        # 5. Update Coordinates & Clusters for the whole user universe
        # Fetch all words for this user
        all_user_infos = UserWordInfo.objects.filter(user=request.user).select_related('word')
        
        # Filter valid words and get vectors
        valid_infos = []
        vectors = []
        word_to_vector_map = {}
        
        for uwi in all_user_infos:
            vec = services.get_word_vector(uwi.word)
            if vec is not None:
                valid_infos.append(uwi)
                vectors.append(vec)
                word_to_vector_map[uwi.word.thai] = vec
        
        if len(vectors) > 2:
            # UMAP (needs sufficient data)
            try:
                # Optimized: UMAP -> Normalization -> Spacing Optimization
                optimized_coords = services.get_optimized_3d_coordinates(vectors)
                
                # Clustering
                word_to_cluster, cluster_labels = services.auto_clustering(
                    [u.word.thai for u in valid_infos], 
                    existing_vectors=word_to_vector_map
                )

                # Update DB objects
                to_update = []
                for i, uwi in enumerate(valid_infos):
                    uwi.x = float(optimized_coords[i][0])
                    uwi.y = float(optimized_coords[i][1])
                    uwi.z = float(optimized_coords[i][2])
                    
                    c_id = word_to_cluster.get(uwi.word.thai)
                    if c_id:
                        uwi.cluster_id = c_id
                        uwi.cluster_label = cluster_labels.get(c_id, "General")
                    
                    to_update.append(uwi)
                
                UserWordInfo.objects.bulk_update(to_update, ['x', 'y', 'z', 'cluster_id', 'cluster_label'])
            except Exception as e:
                print(f"Error updating coordinates: {e}")

        # Refresh the created object from DB to get updated coords if any
        user_word.refresh_from_db()
        return Response(UserWordInfoSerializer(user_word).data, status=status.HTTP_201_CREATED)

class WordSuggestionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        cluster = request.query_params.get('cluster', 'all')
        user_words_qs = UserWordInfo.objects.filter(user=request.user)
        if cluster != 'all':
            user_words_qs = user_words_qs.filter(cluster_id=cluster)
        user_words = user_words_qs.values_list('word__thai', flat=True)
        suggestions = services.suggest_new_words(list(user_words))
        return Response(suggestions)


class QuizWordsView(APIView):
    """Return words due for SRS review."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        count = int(request.query_params.get('count', 10))
        now = timezone.now()

        # Words due: next_review_date is in the past OR null (never reviewed)
        from django.db.models import Q
        due_words = (
            UserWordInfo.objects
            .filter(user=request.user)
            .filter(Q(next_review_date__lte=now) | Q(next_review_date__isnull=True))
            .select_related('word')
            .order_by('?')[:count]
        )

        serializer = UserWordInfoSerializer(due_words, many=True)
        return Response(serializer.data)


class QuizSubmissionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Expecting: word, result, quiz_type, quiz_id
        data = request.data.copy()
        data['user'] = request.user.id
        serializer = QuizResultSerializer(data=data)
        if serializer.is_valid():
            serializer.save()

            # --- SRS Update ---
            word_id = data.get('word')
            result = data.get('result')
            try:
                uwi = UserWordInfo.objects.get(user=request.user, word_id=word_id)
                now = timezone.now()

                if result == 'fail':
                    uwi.srs_level = 0
                    uwi.next_review_date = now  # re-study immediately
                elif result == 'hard':
                    interval = get_srs_interval(uwi.srs_level)
                    uwi.next_review_date = now + interval * 0.5
                elif result == 'good':
                    uwi.srs_level += 1
                    interval = get_srs_interval(uwi.srs_level)
                    uwi.next_review_date = now + interval
                elif result == 'easy':
                    uwi.srs_level += 2
                    interval = get_srs_interval(uwi.srs_level)
                    uwi.next_review_date = now + interval * 1.5

                uwi.last_review_date = now
                uwi.save(update_fields=['srs_level', 'next_review_date', 'last_review_date'])
            except UserWordInfo.DoesNotExist:
                pass  # word not in user's list, skip SRS update

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def _recompute_coordinates(user):
    """Recalculate UMAP coordinates and clusters for all of a user's words."""
    all_user_infos = list(UserWordInfo.objects.filter(user=user).select_related('word'))

    valid_infos = []
    vectors = []
    word_to_vector_map = {}

    for uwi in all_user_infos:
        vec = services.get_word_vector(uwi.word)
        if vec is not None:
            valid_infos.append(uwi)
            vectors.append(vec)
            word_to_vector_map[uwi.word.thai] = vec

    if len(vectors) > 2:
        try:
            optimized_coords = services.get_optimized_3d_coordinates(vectors)
            word_to_cluster, cluster_labels = services.auto_clustering(
                [u.word.thai for u in valid_infos],
                existing_vectors=word_to_vector_map
            )

            for i, uwi in enumerate(valid_infos):
                uwi.x = float(optimized_coords[i][0])
                uwi.y = float(optimized_coords[i][1])
                uwi.z = float(optimized_coords[i][2])

                c_id = word_to_cluster.get(uwi.word.thai)
                if c_id:
                    uwi.cluster_id = c_id
                    uwi.cluster_label = cluster_labels.get(c_id, "General")

            UserWordInfo.objects.bulk_update(
                valid_infos, ['x', 'y', 'z', 'cluster_id', 'cluster_label']
            )
        except Exception as e:
            print(f"Error recomputing coordinates: {e}")


class DeleteWordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, uwi_id):
        try:
            uwi = UserWordInfo.objects.get(id=uwi_id, user=request.user)
        except UserWordInfo.DoesNotExist:
            return Response({"error": "Word not found."}, status=status.HTTP_404_NOT_FOUND)

        word = uwi.word
        uwi.delete()

        # Delete orphan Word if no other users reference it
        if not UserWordInfo.objects.filter(word=word).exists():
            word.delete()

        # Recompute coordinates for remaining words
        _recompute_coordinates(request.user)

        return Response({"status": "deleted"}, status=status.HTTP_200_OK)


class UpdateWordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, uwi_id):
        try:
            uwi = UserWordInfo.objects.get(id=uwi_id, user=request.user)
        except UserWordInfo.DoesNotExist:
            return Response({"error": "Word not found."}, status=status.HTTP_404_NOT_FOUND)

        data = request.data
        french = data.get('french')

        # Update French on the Word model if changed
        if french and french != uwi.word.french:
            uwi.word.french = french
            uwi.word.save(update_fields=['french'])

        # Update flashcard_infos fields
        editable_fields = [
            'romanization', 'word_type', 'french_sentence',
            'thai_sentence', 'sentence_romanization'
        ]
        infos = uwi.flashcard_infos or {}
        for field in editable_fields:
            if field in data:
                infos[field] = data[field]
        uwi.flashcard_infos = infos
        uwi.save(update_fields=['flashcard_infos'])

        uwi.refresh_from_db()
        return Response(UserWordInfoSerializer(uwi).data, status=status.HTTP_200_OK)
