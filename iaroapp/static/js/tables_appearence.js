document.addEventListener("DOMContentLoaded", function () {
    var body = document.body;
    var checkboxes = document.querySelectorAll('input[type="checkbox"][name^="done_"]');
    var rows = document.querySelectorAll('tbody tr');

    // Function to save checkbox state to localStorage
    function saveCheckboxState(checkbox) {
        var checkboxId = checkbox.id;
        var state = checkbox.checked;
        var storageKey = getStorageKey(checkbox); // Updated to include the target branch/card
        var savedStates = JSON.parse(localStorage.getItem(storageKey)) || {};
        savedStates[checkboxId] = state;
        localStorage.setItem(storageKey, JSON.stringify(savedStates));
    }

    // Function to load checkbox states from localStorage
    function loadCheckboxState() {
        checkboxes.forEach(function (checkbox) {
            var storageKey = getStorageKey(checkbox);
            var savedStates = JSON.parse(localStorage.getItem(storageKey)) || {};
            if (checkbox.id in savedStates) {
                checkbox.checked = savedStates[checkbox.id];
                updateRowColor(checkbox);
            }
        });
    }

    // Function to reset checkbox states at midnight
    function resetStateAtMidnight() {
        var now = new Date();
        var midnight = new Date();
        midnight.setHours(24, 0, 0, 0);
        var timeUntilMidnight = midnight.getTime() - now.getTime();

        setTimeout(function () {
            localStorage.clear(); // Clear localStorage at midnight
            location.reload(); // Reload page to reset states
        }, timeUntilMidnight);
    }

    // Function to generate a unique storage key for localStorage based on branch, product, and date
    function getStorageKey(checkbox) {
        var targetBranch = checkbox.closest('.card').querySelector('h6').innerText.trim(); // Get branch name from the card
        var today = new Date().toISOString().split('T')[0]; // Get current date in YYYY-MM-DD format
        return `${targetBranch}_${today}_checkboxStates`;
    }

    // Function to update the row's background color and text color based on checkbox state
    function updateRowColor(checkbox) {
        var row = checkbox.closest('tr');
        var checkboxWrapper = checkbox.closest('.checkbox-wrapper');
        var isDarkPage = body.classList.contains('dark-page');
        var badges = row.querySelectorAll('.badge');

        if (checkboxWrapper && checkbox.checked) {
            row.style.backgroundColor = isDarkPage ? "var(--bs-success-dark)" : "var(--bs-success)";
            badges.forEach(function (badge) {
                badge.style.cssText = "color: white !important";
            });
        } else {
            row.style.backgroundColor = '';
            badges.forEach(function (badge) {
                badge.style.cssText = "";
            });
        }
    }

    // Load the saved checkbox states on page load
    loadCheckboxState();

    checkboxes.forEach(function (checkbox) {
        checkbox.addEventListener('change', function () {
            updateRowColor(this);
            saveCheckboxState(this); // Save the state when changed
        });

        // Trigger the initial state to ensure correct row coloring
        updateRowColor(checkbox);
    });

    rows.forEach(row => {
        row.addEventListener('click', function (event) {
            // Prevent row click event if a move button was clicked
            if (event.target.classList.contains('move-up') || event.target.classList.contains('move-down')) {
                return;
            }

            if (event.target.type !== 'checkbox') {
                var checkbox = this.querySelector('input[type="checkbox"][name^="done_"]');
                if (!checkbox.disabled) {
                    checkbox.checked = !checkbox.checked;
                    checkbox.dispatchEvent(new Event('change'));
                }
            }
        });
    });

    // Observer to detect class changes on the body and update row color accordingly
    var observer = new MutationObserver(function (mutations) {
        mutations.forEach(function (mutation) {
            if (mutation.attributeName === "class") {
                checkboxes.forEach(function (checkbox) {
                    updateRowColor(checkbox);
                });
            }
        });
    });
    var config = { attributes: true };

    // Start observing class changes on the body element
    observer.observe(body, config);

    // Reset checkbox states at midnight
    resetStateAtMidnight();
});
