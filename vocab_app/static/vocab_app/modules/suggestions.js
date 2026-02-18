import { fetchSuggestions } from './api.js';

export async function loadSuggestions() {
    document.getElementById('modal-suggestions').style.display = 'flex';
    const container = document.getElementById('suggestions-list');
    container.innerHTML = '<p>Loading intelligent suggestions...</p>';

    const cluster = document.getElementById('cluster-filter').value;
    const clusterLabel = document.getElementById('cluster-filter').selectedOptions[0]?.textContent || 'All Clusters';
    document.getElementById('suggestions-title').textContent = `AI Suggestions — ${clusterLabel}`;

    try {
        const suggestions = await fetchSuggestions(cluster);

        container.innerHTML = '';
        suggestions.forEach(s => {
            const div = document.createElement('div');
            div.style.display = 'flex';
            div.style.justifyContent = 'space-between';
            div.style.alignItems = 'center';
            div.style.padding = '10px';
            div.style.borderBottom = '1px solid #333';

            div.innerHTML = `
                <span><strong>${s.word}</strong>${s.french ? ` — <em>${s.french}</em>` : ''}</span>
                <button onclick="window.addSuggestedWord('${s.word}')" style="padding: 5px 10px; font-size: 0.8rem;">Add</button>
            `;
            container.appendChild(div);
        });
    } catch (err) {
        console.error(err);
        container.innerHTML = '<p>Failed to load suggestions.</p>';
    }
}
