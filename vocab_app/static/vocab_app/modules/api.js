import { getCookie } from './utils.js';

export async function fetchMapData() {
    const response = await fetch('/map-data/');
    if (!response.ok) throw new Error('Failed to fetch map data');
    return await response.json();
}

export async function fetchPreviewWord(data) {
    const response = await fetch('/preview-word/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(data)
    });
    if (!response.ok) {
        const err = await response.json();
        throw new Error(err.error || "Failed to generate info");
    }
    return await response.json();
}

export async function postAddWord(data) {
    const response = await fetch('/add-word/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(data)
    });
    if (!response.ok) {
        const err = await response.json();
        throw new Error(err.error || "Failed to add word");
    }
    return await response.json();
}

export async function fetchSuggestions(cluster) {
    const response = await fetch(`/suggest-word/?cluster=${encodeURIComponent(cluster)}`);
    if (!response.ok) throw new Error('Failed to fetch suggestions');
    return await response.json();
}

export async function fetchQuizWords(count) {
    const response = await fetch(`/quiz-words/?count=${count}`);
    if (!response.ok) throw new Error('Failed to fetch quiz words');
    return await response.json();
}

export async function submitQuizResult(data) {
    const response = await fetch('/submit-quiz/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(data)
    });
    if (!response.ok) throw new Error('Failed to submit quiz result');
    return await response.json(); // Assuming backend returns something, or just ok
}

export async function deleteWord(id) {
    const response = await fetch(`/delete-word/${id}/`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    });
    if (!response.ok) throw new Error('Failed to delete word');
    return await response.json();
}

export async function updateWord(id, data) {
    const response = await fetch(`/update-word/${id}/`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(data)
    });
    if (!response.ok) throw new Error('Failed to update word');
    return await response.json();
}
