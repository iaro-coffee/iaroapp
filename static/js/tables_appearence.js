// JS for styling tables


document.addEventListener("DOMContentLoaded", function () {
    var body = document.body;
    var checkboxes = document.querySelectorAll('input[type="checkbox"][name^="done_"]');
    var rows = document.querySelectorAll('tbody tr');

    // Func to update row bg-color based on checkbox state
    function updateRowColor(checkbox) {
        var row = checkbox.closest('tr');
        var checkboxWrapper = checkbox.closest('.checkbox-wrapper');
        var isDarkPage = body.classList.contains('dark-page');

        if (checkboxWrapper && checkbox.checked) {
            row.style.backgroundColor = isDarkPage ? "var(--bs-success-dark)" : "var(--bs-success)";
        } else {
            row.style.backgroundColor = '';
        }
    }

    checkboxes.forEach(function (checkbox) {
        checkbox.addEventListener('change', function () {
            updateRowColor(this);
        });

        // Initially trigger
        updateRowColor(checkbox);
    });


    rows.forEach(row => {
        row.addEventListener('click', function (event) {
            if (event.target.type !== 'checkbox') {
                var checkbox = this.querySelector('input[type="checkbox"][name^="done_"]');
                if (!checkbox.disabled) {
                    checkbox.checked = !checkbox.checked;
                    checkbox.dispatchEvent(new Event('change'));
                }
            }
        });
    });

    // Observer to detect class changes on the body
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

    // Start observing
    observer.observe(body, config);
});
