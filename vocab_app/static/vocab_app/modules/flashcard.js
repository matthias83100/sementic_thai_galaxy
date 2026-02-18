import { speak } from './utils.js';
import { deleteWord, updateWord } from './api.js';

let currentWord = null;
let cachedAllWords = null;
let refreshCallback = null;
let isEditMode = false;

export function showFlashcard(wordInfo, allWords, onRefresh) {
    console.log("Showing flashcard for:", wordInfo);
    if (!wordInfo || !wordInfo.word) return;

    currentWord = wordInfo;
    cachedAllWords = allWords;
    refreshCallback = onRefresh;
    isEditMode = false;

    renderFlashcard(allWords);
    document.getElementById('modal-flashcard').style.display = 'flex';
}

function renderFlashcard(allWords) {
    const info = currentWord.flashcard_infos || {};
    const content = document.getElementById('flashcard-content');

    // Process sentence breakdown (only in view mode)
    let sentenceHtml = '';
    if (!isEditMode && info.thai_sentence && info.sub_words) {
        const userWordSet = new Set(allWords.map(w => w.word.thai));
        const coloredWords = info.sub_words.map(w => {
            const isKnown = userWordSet.has(w);
            const color = isKnown ? '#33FF57' : '#FF5733';
            return `<span style="color: ${color}; font-weight: bold; cursor: pointer; margin: 0 2px;" title="${isKnown ? 'Already in list' : 'Click to add'}" onclick="event.stopPropagation(); window.addSuggestedWord('${w}')">${w}</span>`;
        }).join(' ');

        sentenceHtml = `
            <div class="flashcard-detail" style="text-align: center; margin-top: 20px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 20px;">
                <p style="margin-bottom: 10px; color: #aaa; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px;">Example Sentence</p>
                <div style="font-size: 1.25rem; margin-bottom: 12px; color: var(--accent-blue); font-weight: 600;">${info.french_sentence || ''}</div>
                <div style="font-size: 1.5rem; margin-bottom: 8px; line-height: 1.6;">
                    ${coloredWords}
                    <button class="audio-btn" id="btn-audio-sentence">🔊</button>
                </div>
                <div style="color: rgba(255,255,255,0.5); font-style: italic; font-size: 0.95rem; margin-top: 5px;">${info.sentence_romanization || ''}</div>
            </div>
        `;
    } else if (isEditMode) {
        sentenceHtml = `
            <div class="flashcard-detail" style="text-align: left; margin-top: 20px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 20px;">
                <p style="color: #aaa; font-size: 0.7rem; text-transform: uppercase; margin-bottom: 5px;">Edit Sentence</p>
                <input type="text" id="edit-french-sentence" class="flashcard-edit-input" value="${info.french_sentence || ''}" placeholder="French Sentence">
                <input type="text" id="edit-thai-sentence" class="flashcard-edit-input" style="margin-top: 10px;" value="${info.thai_sentence || ''}" placeholder="Thai Sentence">
                <input type="text" id="edit-sentence-romanization" class="flashcard-edit-input" style="margin-top: 10px;" value="${info.sentence_romanization || ''}" placeholder="Sentence Romanization">
            </div>
        `;
    }

    let componentsHtml = '';
    if (!isEditMode) {
        if (info.components && info.components[0]?.length > 0) {
            const [parts, trans] = info.components;
            componentsHtml = `
                <div class="flashcard-detail">
                    <p><strong>Semantic Components:</strong></p>
                    ${parts.map((p, i) => `<span class="component-tag clickable" onclick="event.stopPropagation(); window.filterByComponent('${p}')">${p} (${trans[i]})</span>`).join('')}
                </div>
            `;
        } else {
            const thai = currentWord.word.thai;
            const french = currentWord.word.french;
            componentsHtml = `
                <div class="flashcard-detail">
                    <p><strong>Semantic Components:</strong></p>
                    <span class="component-tag clickable" onclick="event.stopPropagation(); window.filterByComponent('${thai}')">${thai} (${french})</span>
                </div>
            `;
        }
    }

    content.innerHTML = `
        <div class="word-thai">
            ${currentWord.word.thai}
            <button class="audio-btn" id="btn-audio-word">🔊</button>
        </div>
        
        <div class="flashcard-main-info">
            ${isEditMode ?
            `<input type="text" id="edit-romanization" class="flashcard-edit-input" value="${info.romanization || ''}" placeholder="Romanization">` :
            `<div class="romanization">${info.romanization || ''}</div>`
        }
            
            ${isEditMode ?
            `<input type="text" id="edit-french" class="flashcard-edit-input" style="margin-top: 10px; font-size: 1.5rem;" value="${currentWord.word.french}" placeholder="French Translation">` :
            `<div class="translation">${currentWord.word.french}</div>`
        }
        </div>

        <div class="flashcard-detail">
            <p><strong>Type:</strong> 
                ${isEditMode ?
            `<input type="text" id="edit-word-type" class="flashcard-edit-input" style="width: 120px;" value="${info.word_type || ''}" placeholder="Type">` :
            (info.word_type || 'Unknown')
        }
            </p>
        </div>

        ${sentenceHtml}
        ${componentsHtml}

        <div class="flashcard-actions">
            <button class="flashcard-action-btn delete" onclick="window.requestDeleteWord()">🗑️ Delete</button>
            <button class="flashcard-action-btn edit" id="btn-toggle-edit" onclick="window.toggleFlashcardEdit()">
                ${isEditMode ? '💾 Save' : '✏️ Edit'}
            </button>
        </div>
    `;

    // Re-attach listeners
    attachListeners();
}

function attachListeners() {
    const btnWord = document.getElementById('btn-audio-word');
    if (btnWord) {
        btnWord.onclick = async (e) => {
            e.stopPropagation();
            btnWord.classList.add('playing');
            try {
                await speak(currentWord.word.thai);
            } finally {
                btnWord.classList.remove('playing');
            }
        };
    }

    const btnSentence = document.getElementById('btn-audio-sentence');
    if (btnSentence) {
        btnSentence.onclick = async (e) => {
            e.stopPropagation();
            btnSentence.classList.add('playing');
            try {
                await speak(currentWord.flashcard_infos.thai_sentence);
            } finally {
                btnSentence.classList.remove('playing');
            }
        };
    }
}

// Global exposure for flashcard actions
window.requestDeleteWord = () => {
    document.getElementById('modal-delete-confirm').style.display = 'flex';
};

window.confirmDeleteWord = async () => {
    const btn = document.querySelector('#modal-delete-confirm button:first-child');
    const originalText = btn.innerText;

    try {
        btn.disabled = true;
        btn.innerText = "Deleting... ⏳";

        await deleteWord(currentWord.id);
        document.getElementById('modal-delete-confirm').style.display = 'none';
        window.closeModal('modal-flashcard');
        if (refreshCallback) await refreshCallback();
    } catch (err) {
        alert("Failed to delete word: " + err.message);
    } finally {
        btn.disabled = false;
        btn.innerText = originalText;
    }
};

window.cancelDeleteWord = () => {
    document.getElementById('modal-delete-confirm').style.display = 'none';
};

window.toggleFlashcardEdit = async () => {
    if (isEditMode) {
        // Saving changes
        const btn = document.getElementById('btn-toggle-edit');
        const originalText = btn.innerText;

        const updatedData = {
            french: document.getElementById('edit-french').value,
            romanization: document.getElementById('edit-romanization').value,
            word_type: document.getElementById('edit-word-type').value,
            french_sentence: document.getElementById('edit-french-sentence').value,
            thai_sentence: document.getElementById('edit-thai-sentence').value,
            sentence_romanization: document.getElementById('edit-sentence-romanization').value
        };

        try {
            btn.disabled = true;
            btn.innerText = "Saving...";

            const updatedUwi = await updateWord(currentWord.id, updatedData);

            // Update local array to skip full refetch
            if (cachedAllWords) {
                const idx = cachedAllWords.findIndex(w => w.id === currentWord.id);
                if (idx !== -1) {
                    cachedAllWords[idx] = updatedUwi;
                }
            }

            currentWord = updatedUwi;
            isEditMode = false;

            // Trigger UI update in main/renderer with the updated local data
            if (refreshCallback) await refreshCallback(cachedAllWords);

            renderFlashcard(cachedAllWords);
        } catch (err) {
            alert("Failed to update word: " + err.message);
            btn.disabled = false;
            btn.innerText = originalText;
        }
    } else {
        isEditMode = true;
        renderFlashcard(cachedAllWords);
    }
};
