// JS for tasks tables completion status and subtasks redirection


function submitForm() {
    var form = document.querySelector('#tasksForm');
    form.submit()
    window.scrollTo(0, 0);
};

document.addEventListener("DOMContentLoaded", function () {
    let descriptionLinks = document.querySelectorAll('.descriptionLink');
    descriptionLinks.forEach((link) => {
        link.addEventListener('click', function(event) {
            event.preventDefault();
            event.stopPropagation();

            var taskRow = this.closest('.entry');
            var descriptionPlaceholder = taskRow.querySelector('.task-description');

            var isVisible = descriptionPlaceholder.style.display === 'flex';
            descriptionPlaceholder.style.display = isVisible ? 'none' : 'flex';

            if (!isVisible) {
                var descriptionText = this.querySelector('.hidden').textContent;
                descriptionPlaceholder.innerHTML = descriptionText;
            }

            // Directly toggle the SVG for the icon
            var chevronIcon = this.querySelector('svg');
            if (chevronIcon) {
                // Determine the new icon
                var newIcon = isVisible ? 'chevron-right' : 'chevron-down';
                // Remove the existing SVG
                chevronIcon.remove();
                // Create a new span for Feather to target
                var iconSpan = document.createElement('span');
                iconSpan.setAttribute('data-feather', newIcon);
                this.insertBefore(iconSpan, this.firstChild);
                // Reapply Feather to render the new icon
                feather.replace();
            }
        });
    });
});

