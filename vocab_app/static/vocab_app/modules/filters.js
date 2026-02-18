export let activeComponentFilter = null;

export function initFilters(renderer, getAllWords) {
    const clusterSelect = document.getElementById('cluster-filter');
    const typeSelect = document.getElementById('type-filter');
    const addDateSelect = document.getElementById('add-date-filter');
    const reviewDateSelect = document.getElementById('review-date-filter');
    const srsLevelSelect = document.getElementById('srs-level-filter');
    const searchInput = document.getElementById('search-input');

    const update = () => {
        const allWords = getAllWords();
        renderer.updateData(allWords, {
            cluster: clusterSelect.value,
            type: typeSelect.value,
            addDate: addDateSelect.value,
            reviewDate: reviewDateSelect.value,
            srsLevel: srsLevelSelect.value,
            component: activeComponentFilter,
            search: searchInput.value.toLowerCase()
        });
    };

    clusterSelect.onchange = update;
    typeSelect.onchange = update;
    addDateSelect.onchange = update;
    reviewDateSelect.onchange = update;
    srsLevelSelect.onchange = update;
    searchInput.oninput = update;

    return update; // Return update function if needed elsewhere
}

export function filterByComponent(component, renderer, allWords) {
    activeComponentFilter = component;
    document.getElementById('modal-flashcard').style.display = 'none'; // Close flashcard

    // Show banner
    const banner = document.getElementById('component-filter-banner');
    const text = document.getElementById('component-filter-text');
    text.textContent = `Filtering by component: ${component}`;
    banner.classList.remove('hidden');

    // Apply filter
    triggerUpdate(renderer, allWords);
}

export function clearComponentFilter(renderer, allWords) {
    activeComponentFilter = null;
    document.getElementById('component-filter-banner').classList.add('hidden');
    triggerUpdate(renderer, allWords);
}

function triggerUpdate(renderer, allWords) {
    const clusterSelect = document.getElementById('cluster-filter');
    const typeSelect = document.getElementById('type-filter');
    const addDateSelect = document.getElementById('add-date-filter');
    const reviewDateSelect = document.getElementById('review-date-filter');
    const srsLevelSelect = document.getElementById('srs-level-filter');
    const searchInput = document.getElementById('search-input');

    renderer.updateData(allWords, {
        cluster: clusterSelect.value,
        type: typeSelect.value,
        addDate: addDateSelect.value,
        reviewDate: reviewDateSelect.value,
        srsLevel: srsLevelSelect.value,
        component: activeComponentFilter,
        search: searchInput.value.toLowerCase()
    });
}

export function updateClusterDropdown(allWords) {
    const clusterSelect = document.getElementById('cluster-filter');
    const clusters = {};

    allWords.forEach(w => {
        if (w.cluster_id && !clusters[w.cluster_id]) {
            clusters[w.cluster_id] = w.cluster_label || `Cluster ${w.cluster_id}`;
        }
    });

    // Save current selection if possible, currently just resets or keeps if exists
    const currentVal = clusterSelect.value;

    clusterSelect.innerHTML = '<option value="all">All Clusters</option>';
    Object.entries(clusters).forEach(([id, label]) => {
        const opt = document.createElement('option');
        opt.value = id;
        opt.textContent = label;
        clusterSelect.appendChild(opt);
    });

    if (currentVal && Array.from(clusterSelect.options).map(o => o.value).includes(currentVal)) {
        clusterSelect.value = currentVal;
    }
}
