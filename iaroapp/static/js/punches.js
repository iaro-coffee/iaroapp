document.addEventListener("DOMContentLoaded", function () {
    // Function to get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Variables for punch-in modal
    const punchInModal = document.getElementById('punchInModal');
    const punchInForm = document.getElementById('punchInForm');
    const modalUserIdInput = document.getElementById('modalUserId');
    const modalShiftIdInput = document.getElementById('modalShiftId');
    const managerNoteInput = document.getElementById('managerNote');

    // Variables for punch-out
    const punchOutButton = document.getElementById('punchOutButton');
    const submitRatingBtn = document.getElementById('submitRatingBtn');
    const confirmResetBtn = document.getElementById('confirmResetBtn');
    const cancelResetBtn = document.getElementById('cancelResetBtn');

    let resetPending = false;

    // Event listener for all punch-in buttons (multiple shifts)
    document.querySelectorAll('.punchInButton').forEach(function(punchInButton) {
        punchInButton.addEventListener('click', function () {
            // Get user ID and shift ID from button attributes
            const userId = punchInButton.getAttribute('data-user-id');
            const shiftId = punchInButton.getAttribute('data-shift-id');

            // Set hidden inputs in the modal form
            modalUserIdInput.value = userId;
            modalShiftIdInput.value = shiftId;

            // Clear any previous note
            managerNoteInput.value = '';

            // Show the punch-in modal without backdrop
            const modal = new bootstrap.Modal(punchInModal, {
                backdrop: false
            });
            modal.show();
        });
    });

    // Event listener for Punch In form submission
    punchInForm.addEventListener('submit', function (event) {
        event.preventDefault();

        const userId = modalUserIdInput.value;
        const shiftId = modalShiftIdInput.value;
        const managerNote = managerNoteInput.value;

        // Add a console log to verify the note
        console.log('Manager Note:', managerNote);

        // Proceed with punch-in action
        handlePunchAction(userId, 'punch_in', null, managerNote, false, shiftId);

        // Hide the modal after submission
        const modalInstance = bootstrap.Modal.getInstance(punchInModal, {});
        modalInstance.hide();
    });

    // Punch-Out button event listener
    if (punchOutButton) {
        punchOutButton.addEventListener('click', function () {
            // Open the modal for punch-out confirmation, no action taken yet
            // Assuming you have a modal for punch-out (submitModal)
            const submitModal = new bootstrap.Modal(document.getElementById('submitModal'));
            submitModal.show();
        });
    }

    // Submit Rating button event listener (for punch-out)
    if (submitRatingBtn) {
        submitRatingBtn.addEventListener('click', function () {
            const userId = punchOutButton.getAttribute('data-user-id');
            const shiftId = punchOutButton.getAttribute('data-shift-id');
            const rating = document.querySelector('input[name="star"]:checked') ? document.querySelector('input[name="star"]:checked').value : null;
            const comment = document.getElementById('comment').value;

            // Ensure rating is provided
            if (!rating) {
                alert("Please provide a rating before submitting.");
                return;
            }

            // Proceed with punch-out action only after rating is provided
            handlePunchAction(userId, 'punch_out', rating, comment, false, shiftId);

            // Hide the modal after submission
            const submitModalInstance = bootstrap.Modal.getInstance(document.getElementById('submitModal'));
            submitModalInstance.hide();
        });
    }

    // Confirm Reset button event listener
    if (confirmResetBtn) {
        confirmResetBtn.addEventListener('click', function () {
            const userId = punchOutButton.getAttribute('data-user-id');
            const shiftId = punchOutButton.getAttribute('data-shift-id');
            resetPending = false;  // Reset the flag once confirmed
            handlePunchAction(userId, 'punch_out', null, "", true, shiftId);  // Confirm reset
        });
    }

    // Cancel Reset button event listener
    if (cancelResetBtn) {
        cancelResetBtn.addEventListener('click', function () {
            resetPending = false;  // Cancel the reset confirmation
            // Close the modal (assuming you have a function or modal instance)
            const submitModalInstance = bootstrap.Modal.getInstance(document.getElementById('submitModal'));
            submitModalInstance.hide();
        });
    }

    function handlePunchAction(userId, action, rating = null, comment = "", confirmReset = false, shiftId = null) {
        // Do not proceed if reset is pending but not confirmed
        if (resetPending && !confirmReset) {
            console.log('Reset confirmation is pending. Awaiting user action.');
            return;
        }

        const payload = {
            user_id: userId,
            action: action,
            rating: rating,
            comment: comment,  // Include the note or comment
            confirm_reset: confirmReset,
            shift_id: shiftId  // Include shift_id in the payload
        };

        // Add a console log to verify the payload
        console.log('Payload:', payload);

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

    function showResetConfirmation() {
        // Update modal to show reset confirmation instead of punch-out
        document.getElementById('modalTitle').textContent = "Reset Shift Confirmation";
        document.getElementById('punchOutConfirmationSection').style.display = 'none';
        document.getElementById('resetConfirmationSection').style.display = 'block';
        // Open the modal (assuming you have a modal instance)
        const submitModal = new bootstrap.Modal(document.getElementById('submitModal'));
        submitModal.show();
    }
});
