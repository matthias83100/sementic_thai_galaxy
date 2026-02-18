import os
import json
import numpy as np
import pandas as pd
import umap
import tltk
from pythainlp import word_vector
from pythainlp.corpus import thai_words
from pythainlp.tokenize import word_tokenize, syllable_tokenize
from pythainlp.tag import pos_tag
from scipy.spatial.distance import cosine
from scipy.cluster.hierarchy import linkage, fcluster
from openai import OpenAI

# Initialize OpenAI Client (Typhoon)
client = OpenAI(
    api_key=os.environ.get("TYPHOON_API_KEY"),
    base_url="https://api.opentyphoon.ai/v1"
)

# Global variable to store the model
_TH_MODEL = None
_TH_WORD_SET = None

def get_thai_model():
    global _TH_MODEL
    if _TH_MODEL is None:
        print("Loading Thai Word Vector Model...")
        _TH_MODEL = word_vector.WordVector(model_name="thai2fit_wv").get_model()
    return _TH_MODEL

def get_thai_word_set():
    global _TH_WORD_SET
    if _TH_WORD_SET is None:
        _TH_WORD_SET = thai_words()
    return _TH_WORD_SET

# ==========================================
# 1. Flashcard Generation Logic
# ==========================================

def generate_example_sentence_pair(french_word, thai_word):
    prompt = f"""Generate a short, natural French example sentence using the word "{french_word}" (meaning "{thai_word}" in Thai).
    Then provide the natural Thai translation of that sentence.
    
    Return ONLY a JSON object:
    {{
        "french": "string",
        "thai": "string"
    }}"""
    try:
        response = client.chat.completions.create(
            model="typhoon-v2.5-30b-a3b-instruct",
            messages=[
                {"role": "system", "content": "You are a Thai-French linguistic expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Sentence generation error: {e}")
        return {"french": f"C'est {french_word}.", "thai": f"นั่คือ{thai_word}"}

def translate_french_sentence(french_word, thai_word, french_sentence):
    if not french_sentence:
        return ""
    
    examples = [
        {
            "f_word": "Relâcher",
            "t_word": "ปล่อย",
            "f_sent": "Relâcher le petit poisson.",
            "t_trans": "ปล่อยปลาตัวเล็กไป"
        }
    ]

    system_message = (
        "You are an expert French-to-Thai translator. "
        "Task: Translate the French sentence into natural Thai. "
        "Constraint: You MUST use the provided 'Thai Word' to represent the 'French Word'. "
        "Output: Provide only the Thai translation, no explanations."
    )

    prompt = f"<|im_start|>system\n{system_message}<|im_end|>\n"

    for ex in examples:
        prompt += (
            f"<|im_start|>user\n"
            f"### Example\n"
            f"French Word: {ex['f_word']}\n"
            f"Thai Word: {ex['t_word']}\n"
            f"French Sentence: {ex['f_sent']}\n"
            f"Thai Translation:<|im_end|>\n"
            f"<|im_start|>assistant\n{ex['t_trans']}<|im_end|>\n"
        )

    prompt += (
        f"<|im_start|>user\n"
        f"### Task\n"
        f"French Word: {french_word}\n"
        f"Thai Word: {thai_word}\n"
        f"French Sentence: {french_sentence}\n"
        f"Thai Translation:<|im_end|>\n"
        f"<|im_start|>assistant\n"
    )

    try:
        response = client.chat.completions.create(
            model="typhoon-v2.5-30b-a3b-instruct",
            messages=[
                {"role": "system", "content": "You are a Thai-French linguistic expert. You focus on literal component meanings."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
        )
        output = response.choices[0].message.content
        output = output.replace('/ค่ะ','').replace('?','')
        return output
    except Exception as e:
        print(f"Translation error: {e}")
        return ""

def get_word_type(word):
    mapping = {
        'PRON': 'Pronom',
        'NOUN': 'Nom',
        'ADV': 'Adverbe',
        'PART': 'Particule',
        'VERB': 'Verbe',
        'PROPN': 'Nom propre',
        'AUX': 'Auxiliaire',
        'SCONJ': 'Conjonction (sub)',
        'ADJ': 'Adjectif',
        'CCONJ': 'Conjonction (coord)'
    }

    try:
        pos_tags = tltk.nlp.pos_tag(word)
        raw_tag = pos_tags[0][0][1]
        readable_type = mapping.get(raw_tag, "Inconnu")
        
        if readable_type == 'Nom propre':
             # Secondary check
            tokens = word_tokenize(word, engine="newmm")
            # Simple fallback if complex tagging fails or is not available in this context
            # For now, sticking to tltk mostly, but let's try a basic check if needed
            readable_type = 'Inconnu' # Fallback for strictly proper nouns logic in notebook
            # Note: The original notebook used `pos_tag` from pythainlp for the second check
            # We will simplify for stability: if tltk says PROPN, we mark Inconnu/Nom based on logic
            pass
        return readable_type
    except:
        return "Inconnu"

def find_best_split(word, syllables, th_model):
    best_score = -1
    best_parts = None

    # 1. Evaluate Granular Split
    if all(s in th_model for s in syllables):
        vec_word = th_model[word]
        vec_sum = np.sum([th_model[s] for s in syllables], axis=0)
        best_score = 1 - cosine(vec_word, vec_sum)
        best_parts = syllables

    # 2. Evaluate Binary Splits
    for i in range(1, len(syllables)):
        part1 = "".join(syllables[:i])
        part2 = "".join(syllables[i:])

        if part1 in th_model and part2 in th_model:
            vec_word = th_model[word]
            vec_sum = th_model[part1] + th_model[part2]
            score = 1 - cosine(vec_word, vec_sum)

            if score > best_score:
                best_score = score
                best_parts = [part1, part2]

    return best_parts, best_score

def get_french_components(word):
    th_model = get_thai_model()
    th_word_set = get_thai_word_set()
    THRESHOLD = 0.04

    if word not in th_model:
        return None

    syllables_raw = syllable_tokenize(word)
    if len(syllables_raw) == 1:
        return None

    best_parts, score = find_best_split(word, syllables_raw, th_model)
    
    if not best_parts:
        return None

    if score < THRESHOLD:
        return None

    check_dict = [part in th_word_set for part in best_parts]
    if False in check_dict:
        return None

    parts_str = " + ".join(best_parts)
    prompt = f"""Analyze the Thai word "{word}" composed of [{parts_str}].

    1. Is this a 'True Semantic Compound'? (Yes, if the components contribute to the meaning).
    2. Provide the literal French translation for each component separately.
    3. Provide the natural French translation for the whole word.

    Return ONLY a JSON object in this format:
    {{
        "is_true_compound": boolean,
        "component_translations": ["french_1", "french_2"],
        "full_word_french": "string"
    }}"""

    try:
        response = client.chat.completions.create(
            model="typhoon-v2.5-30b-a3b-instruct",
            messages=[
                {"role": "system", "content": "You are a Thai-French linguistic expert. You focus on literal component meanings."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        res = json.loads(response.choices[0].message.content)
        if res.get("is_true_compound"):
            return best_parts, res.get("component_translations", [])
    except Exception as e:
        pass

    return None

def get_flashcard_infos(thai_word, french_word, french_sentence):
    # 1) Handle empty sentence by generating a pair
    if not french_sentence:
        pair = generate_example_sentence_pair(french_word, thai_word)
        french_sentence = pair.get("french", "")
        thai_sentence = pair.get("thai", "")
    else:
        # Translate the provided french sentence
        thai_sentence = translate_french_sentence(french_word, thai_word, french_sentence)
    
    # 2) Tokenize
    sub_words = word_tokenize(thai_sentence)
    
    # 3) Romanization
    # tltk.nlp.th2roman might fail if not fully initialized, ensure tltk is imported
    try:
        romanization = tltk.nlp.th2roman(thai_word).replace(' <s/>', '')
        sentence_romanization = " ".join([tltk.nlp.th2roman(w).replace(' <s/>', '') for w in sub_words])
    except:
        romanization = ""
        sentence_romanization = ""

    # 4) Word Type
    word_type = get_word_type(thai_word)

    # 5) Components
    components = get_french_components(thai_word)

    return {
        "thai_sentence": thai_sentence,
        "french_sentence": french_sentence,
        "sub_words": sub_words,
        "romanization": romanization,
        "sentence_romanization": sentence_romanization,
        "word_type": word_type,
        "components": components
    }

# ==========================================
# 2. Coordinates & Clustering
# ==========================================

def apply_repulsion(coords, min_dist=0.15, iterations=100):
    """
    Iteratively pushes points apart if they are closer than min_dist.
    Constraints points to the unit sphere surface.
    """
    new_coords = coords.copy()
    for it in range(iterations):
        moved = False
        for i in range(len(new_coords)):
            for j in range(i + 1, len(new_coords)):
                p1 = new_coords[i]
                p2 = new_coords[j]
                diff = p1 - p2
                dist = np.linalg.norm(diff)
                
                if dist < min_dist and dist > 1e-6:
                    correction = (diff / dist) * (min_dist - dist) * 0.5
                    new_coords[i] += correction
                    new_coords[j] -= correction
                    moved = True
        
        # Project back to sphere surface
        norms = np.linalg.norm(new_coords, axis=1, keepdims=True)
        new_coords = new_coords / np.where(norms == 0, 1, norms)
        if not moved:
            break
    return new_coords

def get_optimized_3d_coordinates(vectors_list):
    """
    High-level function: UMAP -> Normalization -> Repulsion
    """
    raw_coords = get_3d_coordinates(vectors_list)
    
    # 1. Normalize to unit sphere
    centered = raw_coords - np.mean(raw_coords, axis=0)
    norms = np.linalg.norm(centered, axis=1, keepdims=True)
    initial_sphere_coords = centered / np.where(norms == 0, 1, norms)
    
    # 2. Apply spacing optimization
    final_coords = apply_repulsion(initial_sphere_coords)
    
    return final_coords

def get_3d_coordinates(vectors_list):
    # Vectors list should be a list of lists or numpy array
    reducer = umap.UMAP(n_neighbors=15, n_components=3, min_dist=0.1, metric='cosine', random_state=42)
    embeddings_3d = reducer.fit_transform(vectors_list)
    return embeddings_3d

def get_cluster_label(words_list):
    words_str = ", ".join(words_list)
    prompt = f"""Analyze this list of Thai words: [{words_str}].
    Provide a single, short, descriptive category name for this group (e.g., 'Pronouns', 'Motion Verbs', 'Time Expressions', 'Adjectives').
    Output ONLY the category name.
    """
    try:
        response = client.chat.completions.create(
            model="typhoon-v2.5-30b-a3b-instruct",
            messages=[
                {"role": "system", "content": "You are a linguist assistant. You categorize groups of words accurately."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return "Unknown Category"


def get_word_vector(word_obj):
    """
    Get the vector for a Word object.
    1. If word_obj.vector is set and valid, return it.
    2. Otherwise, load the model, get the vector, save it to word_obj, and return it.
    """
    if word_obj.vector and isinstance(word_obj.vector, list) and len(word_obj.vector) > 0:
        return np.array(word_obj.vector)

    th_model = get_thai_model()
    if word_obj.thai in th_model.key_to_index:
        vec = th_model.get_vector(word_obj.thai)
        # Convert to list for JSON storage
        word_obj.vector = vec.tolist()
        word_obj.save(update_fields=['vector'])
        return vec
    return None

def auto_clustering(words_list, existing_vectors=None):
    """
    words_list: List of word strings.
    existing_vectors: Optional dict mapping word_string -> vector (numpy array).
                      If provided, we use these instead of fetching again.
    """
    th_model = get_thai_model()
    
    # Filter valid words & Collect vectors
    valid_words = []
    vectors = []

    for w in words_list:
        if existing_vectors and w in existing_vectors:
            valid_words.append(w)
            vectors.append(existing_vectors[w])
        elif w in th_model.key_to_index:
            # Fallback if not provided in existing_vectors but exists in model
            # (Though ideally we should call get_word_vector before this function)
            valid_words.append(w)
            vectors.append(th_model.get_vector(w))

    if not valid_words:
        return {}, {}

    vectors = np.array(vectors)
    
    if len(vectors) < 2:
         # Not enough data to cluster
         return {w: 1 for w in valid_words}, {1: "General"}

    Z = linkage(vectors, method='ward')
    max_dist = np.max(Z[:, 2])
    threshold = 0.65 * max_dist
    clusters = fcluster(Z, t=threshold, criterion='distance')

    category_groups = {}
    for word, cluster_id in zip(valid_words, clusters):
        if cluster_id not in category_groups:
            category_groups[cluster_id] = []
        category_groups[cluster_id].append(word)

    cluster_labels = {}
    for cluster_id, words in sorted(category_groups.items()):
        label = get_cluster_label(words)
        cluster_labels[int(cluster_id)] = label

    word_to_cluster = {word: int(cluster_id) for word, cluster_id in zip(valid_words, clusters)}
    
    return word_to_cluster, cluster_labels

# ==========================================
# 3. Suggestions
# ==========================================

def translate_thai_words_to_french(words):
    """Batch translate a list of Thai words to French using the LLM."""
    if not words:
        return {}
    words_str = ", ".join(words)
    prompt = f"""Translate each of these Thai words to French. Return ONLY a JSON object mapping each Thai word to its French translation.
Words: {words_str}

Example format: {{"น้ำ": "eau", "ไฟ": "feu"}}"""
    try:
        response = client.chat.completions.create(
            model="typhoon-v2.5-30b-a3b-instruct",
            messages=[
                {"role": "system", "content": "You are a Thai-French translator. Return only JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Batch translation error: {e}")
        return {}

def suggest_new_words(vocab_list):
    th_model = get_thai_model()
    
    # Filter existing vocab in model
    vocab_list = [w for w in vocab_list if w in th_model.key_to_index]
    if not vocab_list:
        return []

    try:
        similar_words = th_model.most_similar(vocab_list, topn=50)
    except:
        return []

    suggestions = []
    for word, similarity in similar_words:
        if word not in vocab_list:
             suggestions.append({"word": word, "similarity": float(similarity)})
        
        if len(suggestions) >= 10:
            break
    
    # Batch translate all suggested words
    if suggestions:
        words_to_translate = [s["word"] for s in suggestions]
        translations = translate_thai_words_to_french(words_to_translate)
        for s in suggestions:
            s["french"] = translations.get(s["word"], "")
            
    return suggestions

