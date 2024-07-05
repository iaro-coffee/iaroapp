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



window.addEventListener("load", function () {
    hideLoading();
});

// window.addEventListener("beforeunload", function (event) {  // unfortunately deprecated
//     showLoading();
// });
//

window.addEventListener("pageshow", function (event) {
    if (event.persisted) {
        hideLoading();
    }
});

function handleNavigationEvents() {
    document.querySelectorAll('#show-loading').forEach(element => {
        element.addEventListener('click', function (event) {
            showLoading();
            setTimeout(() => {
                window.location.href = element.href;
            }, 100);
            event.preventDefault();
        });
    });
}

document.addEventListener('DOMContentLoaded', handleNavigationEvents);
