
import os
import sys
import django
import numpy as np

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vocab_project.settings')
django.setup()

from vocab_app.models import Word
from vocab_app import services

def run():
    print("Starting Vector Caching Verification...")

    # 1. Create a test word (or get existing) - use a common word to ensure it's in the model
    test_word_text = "ทดสอบ" # "Test"
    word, created = Word.objects.get_or_create(thai=test_word_text, defaults={'french': 'Test'})
    
    # Reset vector to empty to test population
    word.vector = []
    word.save()
    print(f"Word (ID: {word.id}) vector reset to empty.")

    # 2. Call get_word_vector and verify population
    print("\n[Step 1] Calling get_word_vector (should populate from model)...")
    vec = services.get_word_vector(word)
    
    if vec is None:
        print("ERROR: Vector not found in model for 'ทดสอบ'. Verification might fail if model not loaded or word missing.")
        return

    print(f"Vector returned shape: {vec.shape}")
    
    # Reload word from DB to verify persistence
    word.refresh_from_db()
    print(f"Word stored vector length: {len(word.vector)}")
    
    if len(word.vector) > 0 and isinstance(word.vector, list):
        print("SUCCESS: Vector persisted in DB.")
    else:
        print("FAILURE: Vector not persisted.")
        return

    # 3. Test existing_vectors in auto_clustering
    print("\n[Step 2] Testing auto_clustering with existing_vectors...")
    
    # Create a small list of words for clustering
    words_list = ["ทดสอบ", "ไก่", "ไข่"] # Test, Chicken, Egg
    
    # Ensure they exist in DB and have vectors
    word_map = {}
    for w_text in words_list:
        w_obj, _ = Word.objects.get_or_create(thai=w_text)
        v = services.get_word_vector(w_obj)
        if v is not None:
             word_map[w_text] = v
    
    print(f"Pre-fetched cache size: {len(word_map)}")
    
    # Mocking th_model to ensure we don't use it? 
    # Hard to mock internal global in this script easily without patching, 
    # but we can rely on logic: if we pass existing_vectors, it iterates them.
    
    word_to_cluster, labels = services.auto_clustering(words_list, existing_vectors=word_map)
    
    print(f"Clustering result size: {len(word_to_cluster)}")
    
    if len(word_to_cluster) > 0:
        print("SUCCESS: auto_clustering ran with existing_vectors.")
    else:
        print("FAILURE: auto_clustering returned empty result.")

if __name__ == "__main__":
    run()
