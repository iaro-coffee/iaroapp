document.addEventListener('DOMContentLoaded', function () {
    const tasksForm = document.getElementById('tasksForm');
    const tbody = tasksForm.querySelector('tbody');
    const toggleOrderButton = document.getElementById('toggleOrderButton');
    let isEditMode = false;

    function moveRow(row, direction) {
        const sibling = direction === 'up' ? row.previousElementSibling : row.nextElementSibling;
        if (sibling) {
            direction === 'up' ? tbody.insertBefore(row, sibling) : tbody.insertBefore(sibling, row);
            highlightRow(row);
            highlightButtons(row);
        }
    }

    function highlightRow(row) {
        // Remove highlight from all rows
        tbody.querySelectorAll('tr').forEach(r => {
            r.classList.remove('highlighted');
        });

        // Add highlight to the specified row
        row.classList.add('highlighted');
    }

    function highlightButtons(row) {
        // Remove highlight from all buttons
        tbody.querySelectorAll('.move-buttons button').forEach(button => {
            button.classList.remove('move-button-highlighted');
        });

        // Highlight buttons in the moved row
        row.querySelectorAll('.move-buttons button').forEach(button => {
            button.classList.add('move-button-highlighted');
        });
    }

    function resetButtonStyles() {
        document.querySelectorAll('.move-buttons button').forEach(button => {
            button.classList.remove('move-button-highlighted');
        });
    }

    function handleMoveButtonClick(event) {
        const target = event.target;
        if (target.classList.contains('move-up') || target.classList.contains('move-down')) {
            event.stopPropagation();
            const row = target.closest('tr');
            moveRow(row, target.classList.contains('move-up') ? 'up' : 'down');
            resetButtonStyles();
            highlightButtons(row);
            target.blur();
        }
    }

    tbody.addEventListener('click', handleMoveButtonClick);
    tbody.addEventListener('touchend', handleMoveButtonClick);

    toggleOrderButton.addEventListener('click', function () {
        isEditMode = !isEditMode;
        document.querySelectorAll('.move-buttons').forEach(button => {
            button.classList.toggle('d-none', !isEditMode);
            button.classList.toggle('d-table-cell', isEditMode);
        });
        toggleOrderButton.textContent = isEditMode ? 'Submit Order' : 'Edit Order';

        if (!isEditMode) {
            const order = Array.from(tbody.querySelectorAll('tr.entry'))
                .map(row => row.querySelector('input[type="checkbox"]').id.split('_')[1]);
            tasksForm.appendChild(Object.assign(document.createElement('input'), {
                type: 'hidden',
                name: 'order',
                value: order.join(',')
            }));
            tasksForm.submit();
        }
    });

    tasksForm.addEventListener('submit', function (event) {
        if (isEditMode) {
            event.preventDefault();
            toggleOrderButton.click();
        }
    });
});
