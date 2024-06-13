function showLoading() {
    const overlay = document.getElementById('loadingOverlay');
    overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    overlay.classList.remove('active');
    document.body.style.overflow = 'auto';
}

document.addEventListener("DOMContentLoaded", function () {
    hideLoading();
});

window.addEventListener("beforeunload", function () {
    showLoading();
});

window.addEventListener("pageshow", function (event) {
    // Ensure the loading animation is hidden when the page is loaded from the bfcache
    if (event.persisted) {
        hideLoading();
    }
});
