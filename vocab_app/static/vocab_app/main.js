import { GalaxyRenderer } from './renderer.js';
import { fetchMapData } from './modules/api.js';
import { initFilters, filterByComponent, clearComponentFilter, updateClusterDropdown } from './modules/filters.js';
import { showFlashcard } from './modules/flashcard.js';
import { loadSuggestions } from './modules/suggestions.js';
import { setupAddWordListeners } from './modules/addWord.js';
import { setupQuizListeners, handleRating, resetQuizModal } from './modules/quiz.js';

let renderer;
let allWords = [];

// Initialize Application
document.addEventListener('DOMContentLoaded', async () => {
    const isGuest = JSON.parse(document.getElementById('is-guest').textContent);
    renderer = new GalaxyRenderer('container');

    if (isGuest) {
        setupGuestMode();
    }


    // Pass a closure or bound function if needed, but here we just pass the function itself
    // and ensuring it has access to the latest allWords via the module scope or by passing allWords to it.
    // However, showFlashcard needs allWords. renderer.onWordClick passes wordInfo.
    renderer.onWordClick = (wordInfo) => showFlashcard(wordInfo, allWords, refreshMap);

    await refreshMap();

    // Initialize modules
    initFilters(renderer, () => allWords);
    setupAddWordListeners(refreshMap);
    setupQuizListeners(() => allWords);

    // Initial setups
    setupGlobalModals();
    setupReorientButton();
    setupMobileMenu();
    setupProfileDropdown();

    // Expose necessary functions to window for inline HTML handlers or module interop
    exposeGlobals();
});

async function refreshMap(newData = null) {
    try {
        if (newData) {
            allWords = newData;
        } else {
            allWords = await fetchMapData();
        }
        // Get current filter state from DOM elements (handled inside filters.js mostly, but we trigger update here)
        // actually initFilters returns an update function, we might want to grab it or just trigger a change.
        // For simplicity, let's just update data. The standard updateData clears/resets based on args.
        // To respect current filters, we should probably read them or re-trigger the filter logic.
        // Let's rely on filters.js exports or just re-run the filter update if possible, 
        // OR just simple updateData and let the user re-interact if needed, BUT better to preserve state.

        // We can manually trigger the update logic from filters using the DOM state
        const clusterSelect = document.getElementById('cluster-filter');
        const typeSelect = document.getElementById('type-filter');
        const searchInput = document.getElementById('search-input');
        // We need to import activeComponentFilter too if we want to perfect this, 
        // but for now let's just push data and update cluster dropdown.

        renderer.updateData(allWords); // This might reset view if not careful, but updateData usually just updates points.
        updateClusterDropdown(allWords);

        // Trigger a re-filter to apply existing UI filters to new data
        // We can hack this by dispatching an event or calling the filter function if we had the instance.
        // For now, let's just leave it, or dispatch a change event on one of the filters.
        clusterSelect.dispatchEvent(new Event('change'));

    } catch (err) {
        console.error("Failed to fetch map data:", err);
    }
}

function setupGlobalModals() {
    // Modal closing logic
    window.closeModal = (id) => {
        document.getElementById(id).style.display = 'none';
    };

    window.openModal = (id) => {
        document.getElementById(id).style.display = 'flex';
    };

    document.getElementById('btn-suggest').onclick = loadSuggestions;
    document.getElementById('btn-clear-component').onclick = () => clearComponentFilter(renderer, allWords);

    // Quiz quit confirmation logic
    window.requestCloseQuiz = () => {
        const questionStep = document.getElementById('quiz-step-question');
        if (questionStep && !questionStep.classList.contains('hidden')) {
            // Quiz is in progress — show confirmation
            document.getElementById('modal-quit-confirm').style.display = 'flex';
        } else {
            // Not in a quiz (setup or review) — close directly
            window.closeModal('modal-quiz');
        }
    };

    window.confirmQuitQuiz = () => {
        document.getElementById('modal-quit-confirm').style.display = 'none';
        window.closeModal('modal-quiz');
        resetQuizModal();
    };

    window.cancelQuitQuiz = () => {
        document.getElementById('modal-quit-confirm').style.display = 'none';
    };

    // Global rating buttons are handled in quiz.js module
}

function setupReorientButton() {
    const reorientBtn = document.getElementById('btn-reorient');
    reorientBtn.addEventListener('click', () => {
        renderer.resetView();
        reorientBtn.classList.add('spin');
        reorientBtn.addEventListener('animationend', () => reorientBtn.classList.remove('spin'), { once: true });
    });
}

function exposeGlobals() {
    // These are called from HTML onclick attributes generated in JS or HTML
    window.filterByComponent = (component) => filterByComponent(component, renderer, allWords);

    window.addSuggestedWord = (word) => {
        window.closeModal('modal-suggestions');
        window.closeModal('modal-flashcard'); // Close flashcard if open (e.g. from sentence click)
        window.openModal('modal-add-word');
        document.getElementById('add-thai').value = word;
        document.getElementById('add-french').focus();
    };
}



function setupMobileMenu() {
    const toggleBtn = document.getElementById('mobile-menu-toggle');
    const controls = document.querySelector('.controls-group');

    if (toggleBtn && controls) {
        // Toggle menu on click
        toggleBtn.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent closing immediately
            controls.classList.toggle('show');
            toggleBtn.classList.toggle('active');
        });

        // Close menu when clicking outside
        document.addEventListener('click', (e) => {
            if (controls.classList.contains('show') &&
                !controls.contains(e.target) &&
                !toggleBtn.contains(e.target)) {
                controls.classList.remove('show');
                toggleBtn.classList.remove('active');
            }
        });
    }
}

function setupProfileDropdown() {
    const toggle = document.getElementById('user-dropdown-toggle');
    const menu = document.getElementById('user-dropdown-menu');

    if (toggle && menu) {
        toggle.addEventListener('click', (e) => {
            e.stopPropagation();
            menu.classList.toggle('hidden');
        });

        document.addEventListener('click', (e) => {
            if (!menu.classList.contains('hidden') && !toggle.contains(e.target)) {
                menu.classList.add('hidden');
            }
        });
    }
}

function setupGuestMode() {
    // Show Preview Banner
    document.getElementById('preview-banner').classList.remove('hidden');

    // Disable restricted buttons
    const restrictedButtons = ['btn-add-word', 'btn-suggest', 'btn-quiz'];
    restrictedButtons.forEach(id => {
        const btn = document.getElementById(id);
        if (btn) {
            btn.disabled = true;
            btn.style.opacity = '0.5';
            btn.style.cursor = 'not-allowed';
            btn.title = "Register to use this feature";

            // Optionally disable click logic if listeners are already attached
            btn.onclick = (e) => {
                e.preventDefault();
                e.stopPropagation();
            };
        }
    });

    // Disable Suggestion Trigger in Search or other places if any
    // For now the buttons cover most of it.
}
