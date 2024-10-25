// Function to open the shift details modal
function openShiftDetailsModal(branchAddress, comment) {
    const modalContent = document.getElementById('shiftDetailsContent');

    // Display the branch's street address and city
    let contentHTML = `<span class="location text-xs opacity-5">${branchAddress}</span>`;

    // Display comment or default text if no comment is provided
    if (comment && comment.trim() !== "") {
        contentHTML += `<div>Comment: ${comment}</div>`;
    } else {
        contentHTML += `<div>No comment left for this shift.</div>`;
    }

    modalContent.innerHTML = contentHTML;

    const modal = document.getElementById('shiftDetailsModal');
    if (modal) {
        // Ensure modal visibility
        modal.style.display = 'block';
        modal.style.opacity = '0';
        modal.classList.add('show');
        modal.setAttribute('aria-modal', 'true');
        modal.setAttribute('role', 'dialog');
        modal.style.zIndex = '1050';

        // Use a timeout to transition opacity to 1
        setTimeout(() => {
            modal.style.opacity = '1';
            modal.style.transition = 'opacity 0.3s ease-in-out';
        }, 50);  // Slight delay for transition effect

        // Add click listener to close modal when clicking outside content
        modal.addEventListener('click', function (event) {
            if (event.target === modal) {
                closeShiftDetailsModal();
            }
        });
    }
}

// Function to close the shift details modal
function closeShiftDetailsModal() {
    const modal = document.getElementById('shiftDetailsModal');
    if (modal) {
        modal.style.opacity = '0';  // Fade out with opacity
        setTimeout(() => {
            modal.style.display = 'none';
            modal.classList.remove('show');
            modal.removeAttribute('aria-modal');
            modal.removeAttribute('role');
        }, 200);
    }
}
