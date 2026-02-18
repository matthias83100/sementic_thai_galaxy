import { fetchQuizWords, submitQuizResult } from './api.js';
import { shuffle, speak } from './utils.js';

let quizQuestions = [];
let quizResults = [];
let quizCurrentIndex = 0;
let quizSessionId = '';
let currentQuizQuestion = null;
let audioTimeout = null;

const QUIZ_TYPE_LABELS = {
    'fr2th': '🇫🇷→🇹🇭 French to Thai',
    'th2fr': '🇹🇭→🇫🇷 Thai to French',
    'audio': '🔊 Audio Recall',
    'sentence': '📝 Sentence Fill'
};

export function setupQuizListeners(allWordsGetter) {
    document.getElementById('btn-quiz').onclick = () => {
        resetQuizModal();
        document.getElementById('modal-quiz').style.display = 'flex';
    };
    document.getElementById('btn-start-quiz').onclick = () => startQuiz(allWordsGetter());
    document.getElementById('btn-quiz-restart').onclick = () => {
        resetQuizModal();
    };
    document.getElementById('quiz-count').oninput = (e) => {
        document.getElementById('quiz-count-display').textContent = e.target.value;
    };
    document.getElementById('btn-quiz-continue').onclick = () => {
        handleRating('fail');
    };

    // Fix: Add listeners for rating buttons (Hard, Good, Easy, Fail)
    document.querySelectorAll('.rating-btn').forEach(btn => {
        btn.onclick = () => {
            const rating = btn.dataset.rating;
            handleRating(rating);
        };
    });
}

export function resetQuizModal() {
    quizQuestions = [];
    quizResults = [];
    quizCurrentIndex = 0;
    currentQuizQuestion = null;
    document.getElementById('quiz-step-setup').classList.remove('hidden');
    document.getElementById('quiz-step-question').classList.add('hidden');
    document.getElementById('quiz-step-review').classList.add('hidden');
    if (audioTimeout) {
        clearTimeout(audioTimeout);
        audioTimeout = null;
    }
}

async function startQuiz(allWords) {
    const count = parseInt(document.getElementById('quiz-count').value);
    const typeCheckboxes = document.querySelectorAll('.quiz-type-grid input[type="checkbox"]:checked');
    const selectedTypes = Array.from(typeCheckboxes).map(cb => cb.value);

    if (selectedTypes.length === 0) {
        alert('Please select at least one quiz type.');
        return;
    }

    const btn = document.getElementById('btn-start-quiz');
    btn.disabled = true;
    btn.textContent = 'Loading...';

    try {
        const words = await fetchQuizWords(count);

        if (words.length === 0) {
            alert('No words available for quiz. Add some words first!');
            btn.disabled = false;
            btn.textContent = 'Start Quiz';
            return;
        }

        quizSessionId = 'quiz_' + Date.now();
        quizQuestions = words.map(w => generateQuestion(w, selectedTypes, allWords));
        quizResults = [];
        quizCurrentIndex = 0;

        // Switch to question step
        document.getElementById('quiz-step-setup').classList.add('hidden');
        document.getElementById('quiz-step-question').classList.remove('hidden');

        showQuestion();
    } catch (err) {
        console.error('Failed to start quiz:', err);
        alert('Failed to load quiz words.');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Start Quiz';
    }
}

function generateQuestion(wordData, selectedTypes, allWords) {
    const type = selectedTypes[Math.floor(Math.random() * selectedTypes.length)];
    const info = wordData.flashcard_infos || {};

    // Get distractors from allWords (excluding the current word)
    const otherWords = allWords.filter(w => w.word.id !== wordData.word.id);

    switch (type) {
        case 'fr2th': {
            const correctAnswer = wordData.word.thai;
            const distractors = getRandomDistractors(otherWords, 3, 'thai');
            const options = shuffle([correctAnswer, ...distractors]);
            return {
                type,
                wordData,
                prompt: wordData.word.french,
                promptLabel: 'What is the Thai for...',
                correctAnswer,
                options,
                isMCQ: true
            };
        }
        case 'th2fr': {
            const correctAnswer = wordData.word.french;
            const distractors = getRandomDistractors(otherWords, 3, 'french');
            const options = shuffle([correctAnswer, ...distractors]);
            return {
                type,
                wordData,
                prompt: wordData.word.thai,
                promptLabel: 'What is the French for...',
                correctAnswer,
                options,
                isMCQ: true
            };
        }
        case 'audio': {
            const correctAnswer = wordData.word.french;
            const distractors = getRandomDistractors(otherWords, 3, 'french');
            const options = shuffle([correctAnswer, ...distractors]);
            return {
                type,
                wordData,
                prompt: wordData.word.thai, // Will be spoken
                promptLabel: 'Listen and choose the meaning...',
                correctAnswer,
                options,
                isMCQ: true,
                isAudioMCQ: true
            };
        }
        case 'sentence': {
            const thaiSentence = info.thai_sentence || '';
            const thai = wordData.word.thai;

            if (thaiSentence && thaiSentence.includes(thai)) {
                // Create fill-in-the-blank
                const blankedSentence = thaiSentence.replace(thai, '___');
                const correctAnswer = thai;
                const distractors = getRandomDistractors(otherWords, 3, 'thai');
                const options = shuffle([correctAnswer, ...distractors]);
                return {
                    type,
                    wordData,
                    prompt: blankedSentence,
                    promptLabel: 'Fill in the blank',
                    promptContext: info.french_sentence || '',
                    correctAnswer,
                    options,
                    isMCQ: true,
                    isSentence: true
                };
            } else {
                // Fallback to fr2th
                const correctAnswer = wordData.word.thai;
                const distractors = getRandomDistractors(otherWords, 3, 'thai');
                const options = shuffle([correctAnswer, ...distractors]);
                return {
                    type: 'fr2th',
                    wordData,
                    prompt: wordData.word.french,
                    promptLabel: 'What is the Thai for...',
                    correctAnswer,
                    options,
                    isMCQ: true
                };
            }
        }
        default: {
            const correctAnswer = wordData.word.thai;
            const distractors = getRandomDistractors(otherWords, 3, 'thai');
            const options = shuffle([correctAnswer, ...distractors]);
            return {
                type: 'fr2th',
                wordData,
                prompt: wordData.word.french,
                promptLabel: 'What is the Thai for...',
                correctAnswer,
                options,
                isMCQ: true
            };
        }
    }
}

function getRandomDistractors(otherWords, count, field) {
    const shuffled = [...otherWords].sort(() => Math.random() - 0.5);
    const distractors = [];
    const seen = new Set();

    for (const w of shuffled) {
        const val = w.word[field];
        if (val && !seen.has(val)) {
            distractors.push(val);
            seen.add(val);
        }
        if (distractors.length >= count) break;
    }

    while (distractors.length < count) {
        distractors.push('—');
    }
    return distractors;
}

function showQuestion() {
    // Stop any previous audio (e.g. from previous answer)
    if (window.speechSynthesis) window.speechSynthesis.cancel();
    if (audioTimeout) {
        clearTimeout(audioTimeout);
        audioTimeout = null;
    }

    const q = quizQuestions[quizCurrentIndex];
    currentQuizQuestion = q;
    const total = quizQuestions.length;

    const pct = ((quizCurrentIndex) / total) * 100;
    document.getElementById('quiz-progress-bar').style.width = pct + '%';
    document.getElementById('quiz-progress-label').textContent = `${quizCurrentIndex + 1} / ${total}`;
    document.getElementById('quiz-type-label').textContent = QUIZ_TYPE_LABELS[q.type] || q.type;

    document.getElementById('quiz-rating').classList.add('hidden');
    document.getElementById('quiz-rating').classList.add('hidden');
    document.getElementById('quiz-continue').classList.add('hidden');

    // Reset Fail button visibility (it might have been hidden if previous answer was correct)
    const failBtn = document.querySelector('.rating-btn.rating-fail');
    if (failBtn) failBtn.style.display = '';

    const promptEl = document.getElementById('quiz-question-prompt');
    if (q.isSentence) {
        promptEl.innerHTML = `
            <div class="prompt-label">${q.promptLabel}</div>
            ${q.promptContext ? `<div style="color: var(--accent-blue); font-size: 0.95rem; margin-bottom: 8px;">${q.promptContext}</div>` : ''}
            <div class="prompt-sentence">${q.prompt.replace('___', '<span class="blank">&nbsp;&nbsp;&nbsp;&nbsp;</span>')}</div>
        `;
    } else {
        promptEl.innerHTML = `
            <div class="prompt-label">${q.promptLabel}</div>
            <div class="prompt-word">${q.prompt}</div>
        `;
    }

    const optionsEl = document.getElementById('quiz-options');
    optionsEl.innerHTML = '';

    if (q.isAudioMCQ) {
        // Audio Prompt Button
        promptEl.innerHTML = `
            <div class="prompt-label">${q.promptLabel}</div>
            <button id="btn-play-audio" class="quiz-option-btn" style="margin: 20px auto; width: auto; padding: 10px 30px;">
                🔊 Play Audio
            </button>
        `;
        document.getElementById('btn-play-audio').onclick = async () => {
            const btn = document.getElementById('btn-play-audio');
            if (audioTimeout) clearTimeout(audioTimeout);
            btn.classList.add('playing');
            try {
                await speak(q.prompt);
            } finally {
                btn.classList.remove('playing');
            }
        };
        // Auto-play once
        audioTimeout = setTimeout(async () => {
            const btn = document.getElementById('btn-play-audio');
            if (btn) btn.classList.add('playing');
            try {
                // Check if we are still on the same question before speaking
                if (currentQuizQuestion === q) {
                    await speak(q.prompt);
                }
            } finally {
                if (btn) btn.classList.remove('playing');
            }
        }, 500);
    }

    if (q.isMCQ && q.options) {
        q.options.forEach(opt => {
            const btn = document.createElement('button');
            btn.className = 'quiz-option-btn';
            btn.textContent = opt;
            btn.onclick = () => handleQuizAnswer(opt, q);
            optionsEl.appendChild(btn);
        });
    } else if (q.isAudio) { // Legacy or other types if needed
        const revealBtn = document.createElement('button');
        revealBtn.className = 'quiz-option-btn';
        revealBtn.style.gridColumn = '1 / -1';
        revealBtn.textContent = '👁️ Reveal Answer';
        revealBtn.onclick = () => {
            revealBtn.textContent = q.revealText;
            revealBtn.classList.add('correct');
            revealBtn.disabled = true;
            document.getElementById('quiz-rating').classList.remove('hidden');
        };
        optionsEl.appendChild(revealBtn);
    }
}



// Global exposure for rating buttons to call
export async function handleRating(rating) {
    console.log('handleRating called with:', rating);
    const q = currentQuizQuestion;
    if (!q) {
        console.error('No current question!');
        return;
    }

    const result = {
        wordData: q.wordData,
        type: q.type,
        rating,
        wasCorrect: q._wasCorrect !== undefined ? q._wasCorrect : (rating === 'good' || rating === 'easy'),
        selectedAnswer: q._selectedAnswer || null
    };
    quizResults.push(result);

    // Optimistic UI update - move to next immediately
    // We start the network request but don't await the UI transition logic for it
    submitQuizResult({
        word: q.wordData.word.id,
        quiz_type: q.type,
        result: rating,
        quiz_id: quizSessionId
    }).catch(err => console.error('Failed to submit quiz result:', err));

    quizCurrentIndex++;
    if (quizCurrentIndex < quizQuestions.length) {
        showQuestion();
    } else {
        showQuizReview();
    }
}

function handleQuizAnswer(selected, question) {
    console.log('Answer selected:', selected);

    // Reveal Thai word for Audio MCQ
    if (question.isAudioMCQ) {
        const promptEl = document.getElementById('quiz-question-prompt');
        if (!promptEl.querySelector('.revealed-thai-word')) {
            const wordDiv = document.createElement('div');
            wordDiv.className = 'prompt-word revealed-thai-word';
            wordDiv.textContent = question.wordData.word.thai; // Ensure we show the Thai word
            wordDiv.style.marginTop = '15px';
            promptEl.appendChild(wordDiv);
        }
    }

    // Add Audio Button on Reveal (Consistent for all types)
    const promptEl = document.getElementById('quiz-question-prompt');
    const existingAudioBtn = promptEl.querySelector('.revealed-audio-btn');

    // Determine what to speak (Always prefer Thai for learning context)
    let textToSpeak = '';
    if (question.type === 'fr2th') textToSpeak = question.correctAnswer; // Thai
    else if (question.type === 'th2fr') textToSpeak = question.prompt; // Thai
    else if (question.type === 'audio') textToSpeak = question.wordData.word.thai;
    else if (question.isSentence) textToSpeak = question.correctAnswer; // Thai word in blank

    // If it's an audio quiz, we might already have a "Play Audio" button from the question prompt.
    // However, for consistency in the "answered" state, we might want a standard small button next to the revealed text.
    // Let's remove the large "Play Audio" button if it exists and replace/keep a standard one.

    if (question.isAudioMCQ) {
        // Optionally remove the big button to clean up UI, or leave it. 
        // Let's leave the big button as it is the "Prompt". 
        // But we want to ensure the USER can hear the *word* again if they want, 
        // maybe the big button is enough? 
        // Actually, the big button plays `question.prompt` which is the Thai word.
        // So we don't strictly *need* another button if the big one is still there.
        // BUT, the user request says "Play word button is very important".
        // Let's ensure there is *at least* one clearly visible button.
        // If we added a revealed word, let's add a small speaker next to it for consistency with other modes.
    }

    if (!existingAudioBtn) {
        addAudioButton(promptEl, textToSpeak);
    } else {
        // Update the existing button just in case (though unlikely to change)
        existingAudioBtn.onclick = async (e) => {
            e.stopPropagation();
            existingAudioBtn.classList.add('playing');
            try {
                await speak(textToSpeak);
            } finally {
                existingAudioBtn.classList.remove('playing');
            }
        };
    }

    // console.log('Correct Answer:', question.correctAnswer);

    // Ensure we compare strings properly (trim whitespace)
    const s1 = String(selected).trim();
    const s2 = String(question.correctAnswer).trim();
    const isCorrect = s1 === s2;
    // console.log('Is Correct?', isCorrect);

    // Fix: Only select option buttons inside the options container
    const optionsEl = document.getElementById('quiz-options');
    const optionBtns = optionsEl.querySelectorAll('.quiz-option-btn');

    optionBtns.forEach(btn => {
        btn.disabled = true;
        const btnText = String(btn.textContent).trim();
        if (btnText === s2) {
            btn.classList.add('correct');
        }
        if (btnText === s1 && !isCorrect) {
            btn.classList.add('incorrect');
        }
    });

    currentQuizQuestion._wasCorrect = isCorrect;
    currentQuizQuestion._selectedAnswer = selected;

    const ratingSection = document.getElementById('quiz-rating');
    const continueSection = document.getElementById('quiz-continue');

    ratingSection.classList.add('hidden');
    continueSection.classList.add('hidden');

    if (isCorrect) {
        ratingSection.classList.remove('hidden');
        // Fix: Hide "Fail" button if answer is correct
        const failBtn = document.querySelector('.rating-btn.rating-fail');
        if (failBtn) failBtn.style.display = 'none';

        // Auto-play audio on correct answer for reinforcement (Optional, but good for "hearing" the right answer)
        // speak(textToSpeak); 
    } else {
        continueSection.classList.remove('hidden');
        // Re-ensure listener is bound (just in case)
        const contBtn = document.getElementById('btn-quiz-continue');
        contBtn.onclick = () => {
            // console.log('Continue button clicked');
            handleRating('fail');
        };
    }
}

function addAudioButton(container, text) {
    const audioBtn = document.createElement('button');
    audioBtn.className = 'audio-btn revealed-audio-btn';
    audioBtn.innerHTML = '🔊';
    audioBtn.style.fontSize = '1.5rem';
    audioBtn.style.marginTop = '10px';
    audioBtn.title = 'Play Audio';
    audioBtn.onclick = async (e) => {
        e.stopPropagation();
        audioBtn.classList.add('playing');
        try {
            await speak(text);
        } finally {
            audioBtn.classList.remove('playing');
        }
    };
    container.appendChild(audioBtn);
}

function showQuizReview() {
    document.getElementById('quiz-step-question').classList.add('hidden');
    document.getElementById('quiz-step-review').classList.remove('hidden');

    const total = quizResults.length;
    const correct = quizResults.filter(r => r.wasCorrect).length;
    const incorrect = total - correct;
    const pct = total > 0 ? Math.round((correct / total) * 100) : 0;

    document.getElementById('quiz-score-summary').innerHTML = `
        <div class="score-card score-correct">
            <div class="score-value">${correct}</div>
            <div class="score-label">Correct</div>
        </div>
        <div class="score-card score-incorrect">
            <div class="score-value">${incorrect}</div>
            <div class="score-label">Incorrect</div>
        </div>
        <div class="score-card score-total">
            <div class="score-value">${pct}%</div>
            <div class="score-label">Score</div>
        </div>
    `;

    const listEl = document.getElementById('quiz-review-list');
    listEl.innerHTML = '';

    quizResults.forEach(r => {
        const badgeClass = r.wasCorrect ? 'badge-correct' : 'badge-incorrect';
        const ratingClass = `rating-tag-${r.rating}`;
        const typeEmoji = QUIZ_TYPE_LABELS[r.type]?.split(' ')[0] || '';

        const item = document.createElement('div');
        item.className = 'review-item';
        item.innerHTML = `
            <div class="review-badge ${badgeClass}"></div>
            <span class="review-word">${r.wordData.word.thai}</span>
            <span class="review-translation">${r.wordData.word.french}</span>
            <span style="font-size: 0.8rem; opacity: 0.6;">${typeEmoji}</span>
            <span class="review-rating ${ratingClass}">${r.rating}</span>
        `;
        listEl.appendChild(item);
    });

    document.getElementById('quiz-progress-bar').style.width = '100%';
}
