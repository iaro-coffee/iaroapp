// JS for styling tables


document.addEventListener("DOMContentLoaded", function () {
    // Background for done tasks
    var checkboxes = document.querySelectorAll('input[type="checkbox"][name^="done_"]');
    var rows = document.querySelectorAll('tbody tr');

    checkboxes.forEach(function (checkbox) {
        checkbox.addEventListener('change', function () {
            var row = this.closest('tr');
            var checkboxWrapper = this.closest('.checkbox-wrapper');
            if (checkboxWrapper && this.checked) {
                row.style.backgroundColor = "#e7e7e9";
            } else {
                row.style.backgroundColor = '';
            }
        });

        checkbox.dispatchEvent(new Event('change'));
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
});