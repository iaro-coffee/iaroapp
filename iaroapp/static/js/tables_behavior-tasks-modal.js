// JS for tasks tables completion status and subtasks redirection


function submitForm() {
    var form = document.querySelector('#tasksForm');
    form.submit()
    window.scrollTo(0, 0);
};

document.addEventListener("DOMContentLoaded", function () {
    var submitTasksModal = new bootstrap.Modal(document.getElementById("submitTasksModal"), {});
    var infoModal = new bootstrap.Modal(document.getElementById("infoModal"), {});

    document.getElementById('tasksForm').onsubmit = function (evt) {
        evt.preventDefault();
        submitTasksModal.show();
    }

    document.getElementById('confirmSubmit').onclick = function () {
        submitForm();
        submitTasksModal.hide();
    }

    // Hook description modal to button
    let descriptionLinks = document.querySelectorAll('.descriptionLink svg');
    descriptionLinks.forEach((link) => {
        link.addEventListener('click', (event) => {
            event.preventDefault();
            event.stopPropagation();  // Add this line to stop affecting checkbox when opening modal
            var descriptionText = event.target.nextElementSibling.textContent;
            var infoModalContent = document.querySelector('.infoModalContent').innerHTML = descriptionText;
            infoModal.show();
        });
    });

    // Add click event listener to labels with class 'subtasks'
    let subtaskLabels = document.querySelectorAll('.subtasks');
    subtaskLabels.forEach((label) => {
        label.addEventListener('click', function (event) {
            event.preventDefault();
            if (event.target.nodeName !== "svg") {
                // Get the task ID from the closest parent element that has an 'id' attribute
                const taskId = this.querySelector('input[name="id"]');
                const params = new URLSearchParams(window.location.search);
                const searchString = '?' + params.toString();
                // Redirect to the task page
                window.location.href = '/tasks/' + taskId.value + searchString;
            }
            ;
        });
    });

})