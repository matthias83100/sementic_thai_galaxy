export function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

export function shuffle(array) {
    const a = [...array];
    for (let i = a.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
}

// Helper to load voices (wait for them to be ready)
const waitForVoices = () => {
    return new Promise((resolve) => {
        const voices = window.speechSynthesis.getVoices();
        if (voices.length > 0) {
            resolve(voices);
            return;
        }
        window.speechSynthesis.onvoiceschanged = () => {
            const voices = window.speechSynthesis.getVoices();
            resolve(voices);
        };
    });
};

export async function speak(text, lang = 'th-TH') {
    if (!window.speechSynthesis) {
        console.warn('Web Speech API not supported');
        return Promise.resolve();
    }

    // Cancel any current speaking to avoid queue buildup if spamming
    // window.speechSynthesis.cancel(); 
    // Actually, canceling here might be too aggressive if we want to chain, 
    // but for this app's "play word" context, we usually want immediate feedback for the *new* click.
    window.speechSynthesis.cancel();

    const voices = await waitForVoices();
    const utterance = new SpeechSynthesisUtterance(text);

    // Try to find a specific voice for the language
    // Priority: Google Thai, Microsoft Niwat/Premwadee (common on Windows), then any matching lang
    const voice = voices.find(v => v.lang === lang && (v.name.includes('Google') || v.name.includes('Thai')))
        || voices.find(v => v.lang === lang);

    if (voice) {
        utterance.voice = voice;
    }
    utterance.lang = lang;
    utterance.rate = 0.8; // Slightly slower for clarity

    return new Promise((resolve, reject) => {
        utterance.onend = () => resolve();
        utterance.onerror = (e) => reject(e);
        window.speechSynthesis.speak(utterance);
    });
}
