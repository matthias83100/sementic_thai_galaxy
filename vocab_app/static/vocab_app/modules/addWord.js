import { fetchPreviewWord, postAddWord } from './api.js';

let cachedPreviewData = null;

export function setupAddWordListeners(refreshCallback) {
    document.getElementById('btn-add-word').onclick = () => {
        resetAddWordModal();
        document.getElementById('modal-add-word').style.display = 'flex';
    };
    document.getElementById('btn-generate-preview').onclick = handleGeneratePreview;
    document.getElementById('btn-confirm-add').onclick = () => handleConfirmAdd(refreshCallback);
    document.getElementById('btn-back-to-input').onclick = showInputStep;
}

function resetAddWordModal() {
    document.getElementById('add-thai').value = '';
    document.getElementById('add-french').value = '';
    document.getElementById('add-sentence').value = '';
    cachedPreviewData = null;
    showInputStep();
}

function showInputStep() {
    document.getElementById('add-step-input').classList.remove('hidden');
    document.getElementById('add-step-review').classList.add('hidden');
}

function showReviewStep() {
    document.getElementById('add-step-input').classList.add('hidden');
    document.getElementById('add-step-review').classList.remove('hidden');
}

async function handleGeneratePreview() {
    const thai = document.getElementById('add-thai').value;
    const french = document.getElementById('add-french').value;
    const sentence = document.getElementById('add-sentence').value;
    const btn = document.getElementById('btn-generate-preview');

    if (!thai || !french) return alert("Thai and French words are required");

    btn.disabled = true;
    btn.textContent = "Generating...";

    try {
        cachedPreviewData = await fetchPreviewWord({ thai, french, sentence });

        // Populate editable review fields
        document.getElementById('review-romanization').value = cachedPreviewData.romanization || '';
        document.getElementById('review-word-type').value = cachedPreviewData.word_type || '';
        document.getElementById('review-french-sentence').value = cachedPreviewData.french_sentence || '';
        document.getElementById('review-thai-sentence').value = cachedPreviewData.thai_sentence || '';
        document.getElementById('review-sentence-romanization').value = cachedPreviewData.sentence_romanization || '';

        const comps = cachedPreviewData.components || [[], []];
        document.getElementById('review-components-parts').value = (comps[0] || []).join(', ');
        document.getElementById('review-components-trans').value = (comps[1] || []).join(', ');

        showReviewStep();
    } catch (err) {
        console.error(err);
        alert(err.message || "Error generating preview");
    } finally {
        btn.disabled = false;
        btn.textContent = "Generate Info";
    }
}

async function handleConfirmAdd(refreshCallback) {
    const thai = document.getElementById('add-thai').value;
    const french = document.getElementById('add-french').value;
    const sentence = document.getElementById('add-sentence').value;
    const btn = document.getElementById('btn-confirm-add');

    const flashcard_infos = {
        ...cachedPreviewData,
        romanization: document.getElementById('review-romanization').value,
        word_type: document.getElementById('review-word-type').value,
        french_sentence: document.getElementById('review-french-sentence').value,
        thai_sentence: document.getElementById('review-thai-sentence').value,
        sentence_romanization: document.getElementById('review-sentence-romanization').value,
        components: [
            document.getElementById('review-components-parts').value.split(',').map(s => s.trim()).filter(Boolean),
            document.getElementById('review-components-trans').value.split(',').map(s => s.trim()).filter(Boolean)
        ],
    };

    btn.disabled = true;
    btn.textContent = "Saving...";

    try {
        await postAddWord({ thai, french, sentence, flashcard_infos });
        document.getElementById('modal-add-word').style.display = 'none';
        resetAddWordModal();
        if (refreshCallback) await refreshCallback();
    } catch (err) {
        console.error(err);
        alert(err.message || "Failed to add word");
    } finally {
        btn.disabled = false;
        btn.textContent = "Confirm & Add";
    }
}
