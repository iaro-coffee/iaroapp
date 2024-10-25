document.addEventListener("DOMContentLoaded", function () {
    const punchInButton = document.getElementById('punchInButton');
    const punchOutButton = document.getElementById('punchOutButton');
    const submitRatingBtn = document.getElementById('submitRatingBtn');
    const confirmResetBtn = document.getElementById('confirmResetBtn');
    const cancelResetBtn = document.getElementById('cancelResetBtn');

    let resetPending = false;

    if (punchInButton) {
        punchInButton.addEventListener('click', function () {
            const userId = punchInButton.getAttribute('data-user-id');
            handlePunchAction(userId, 'punch_in');
        });
    }

    if (punchOutButton) {
        punchOutButton.addEventListener('click', function () {
            // Open the modal for punch-out confirmation, no action taken yet
            openModal('submitModal');
        });
    }

    if (submitRatingBtn) {
        submitRatingBtn.addEventListener('click', function () {
            const userId = punchOutButton.getAttribute('data-user-id');
            const rating = document.querySelector('input[name="star"]:checked') ? document.querySelector('input[name="star"]:checked').value : null;
            const comment = document.getElementById('comment').value;

            // Ensure rating is provided
            if (!rating) {
                alert("Please provide a rating before submitting.");
                return;
            }

            // Proceed with punch-out action only after rating is provided
            handlePunchAction(userId, 'punch_out', rating, comment);
        });
    }

    if (confirmResetBtn) {
        confirmResetBtn.addEventListener('click', function () {
            const userId = punchOutButton.getAttribute('data-user-id');
            resetPending = false;  // Reset the flag once confirmed
            handlePunchAction(userId, 'punch_out', null, "", true);  // Confirm reset
        });
    }

    if (cancelResetBtn) {
        cancelResetBtn.addEventListener('click', function () {
            resetPending = false;  // Cancel the reset confirmation
            closeModal('submitModal');
        });
    }

    function handlePunchAction(userId, action, rating = null, comment = "", confirmReset = false) {
        // Do not proceed if reset is pending but not confirmed
        if (resetPending && !confirmReset) {
            console.log('Reset confirmation is pending. Awaiting user action.');
            return;
        }

        const payload = {
            user_id: userId,
            action: action,
            rating: rating,
            comment: comment,
            confirm_reset: confirmReset  // Pass confirm_reset flag
        };

        fetch('/shifts/manage/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(payload)
        })
        .then(response => response.json())
        .then(data => {
            console.log('Received response data:', data);

            if (data.status === 'warning' && data.requires_confirmation) {
                // Shift is less than 2 minutes; show reset confirmation
                console.log('Displaying reset confirmation section.');
                resetPending = true;  // Set the flag for pending reset confirmation
                showResetConfirmation();
            } else if (data.status === 'success' || confirmReset) {
                // If success or reset confirmation, refresh the page
                location.reload();
            } else {
                alert('An error occurred: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function showResetConfirmation() {
        // Update modal to show reset confirmation instead of punch-out
        document.getElementById('modalTitle').textContent = "Reset Shift Confirmation";
        document.getElementById('punchOutConfirmationSection').style.display = 'none';
        document.getElementById('resetConfirmationSection').style.display = 'block';
        openModal('submitModal');
    }

    function openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'block';
            modal.setAttribute('aria-modal', 'true');
            modal.setAttribute('role', 'dialog');
        }
    }

    function closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'none';
            modal.removeAttribute('aria-modal');
            modal.removeAttribute('role');
        }
    }
});
