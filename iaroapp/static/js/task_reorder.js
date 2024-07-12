document.addEventListener('DOMContentLoaded', function () {
    const tasksForm = document.getElementById('tasksForm');
    const tbody = tasksForm.querySelector('tbody');
    const toggleOrderButton = document.getElementById('toggleOrderButton');
    let isEditMode = false;

    function moveUp(row) {
        const prev = row.previousElementSibling;
        if (prev) {
            tbody.insertBefore(row, prev);
        }
    }

    function moveDown(row) {
        const next = row.nextElementSibling;
        if (next) {
            tbody.insertBefore(next, row);
        }
    }

    tbody.addEventListener('click', function (event) {
        if (event.target.classList.contains('move-up')) {
            event.stopPropagation();
            const row = event.target.closest('tr');
            moveUp(row);
            event.target.blur();
        } else if (event.target.classList.contains('move-down')) {
            event.stopPropagation();
            const row = event.target.closest('tr');
            moveDown(row);
            event.target.blur();
        }
    });

    toggleOrderButton.addEventListener('click', function () {
        const moveButtons = document.querySelectorAll('.move-buttons');
        isEditMode = !isEditMode;
        moveButtons.forEach(button => {
            button.classList.toggle('d-none', !isEditMode);
            button.classList.toggle('d-table-cell', isEditMode);
        });
        toggleOrderButton.textContent = isEditMode ? 'Submit Order' : 'Edit Order';

        if (!isEditMode) {
            const order = [];
            tbody.querySelectorAll('tr.entry').forEach((row, index) => {
                const checkbox = row.querySelector('input[type="checkbox"]');
                if (checkbox) {
                    const taskId = checkbox.id.split('_')[1];
                    if (taskId) {
                        order.push(taskId);
                    }
                }
            });
            const orderInput = document.createElement('input');
            orderInput.type = 'hidden';
            orderInput.name = 'order';
            orderInput.value = order.join(',');
            tasksForm.appendChild(orderInput);
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
