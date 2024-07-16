document.addEventListener('DOMContentLoaded', function () {
    const orderForm = document.getElementById('orderForm');
    const tasksForm = document.getElementById('tasksForm');
    const tbody = tasksForm.querySelector('tbody');
    const toggleOrderButton = document.getElementById('toggleOrderButton');
    let isEditMode = false;

    function moveRow(row, direction) {
        const sibling = direction === 'up' ? row.previousElementSibling : row.nextElementSibling;
        if (sibling) {
            direction === 'up' ? tbody.insertBefore(row, sibling) : tbody.insertBefore(sibling, row);
            highlightRow(row);
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
            target.blur();
        }
    }

    function adjustPadding(isEditMode) {
        document.querySelectorAll('td').forEach(td => {
            td.style.paddingLeft = !isEditMode ? '10px' : '0px';
        });
    }

    tbody.addEventListener('click', handleMoveButtonClick);
    tbody.addEventListener('touchend', handleMoveButtonClick);

    toggleOrderButton.addEventListener('click', function () {
        isEditMode = !isEditMode;
        document.querySelectorAll('.move-buttons').forEach(button => {
            button.classList.toggle('d-none', !isEditMode);
            button.classList.toggle('d-table-cell', isEditMode);
        });

        document.querySelectorAll('.move-header').forEach(header => {
            header.classList.toggle('d-none', !isEditMode);
            header.classList.toggle('d-table-cell', isEditMode);
        });

        adjustPadding(isEditMode);

        toggleOrderButton.textContent = isEditMode ? 'Submit Order' : 'Edit Order';

        if (!isEditMode) {
            const order = Array.from(tbody.querySelectorAll('tr.entry'))
                .map(row => {
                    const checkbox = row.querySelector('input[type="checkbox"]');
                    return checkbox ? checkbox.id.split('_')[1] : row.dataset.id;
                });
            document.getElementById('orderInput').value = order.join(',');
            orderForm.submit();
        }
    });

    tasksForm.addEventListener('submit', function (event) {
        if (isEditMode) {
            event.preventDefault();
            toggleOrderButton.click();
        }
    });

    adjustPadding(isEditMode);
});
