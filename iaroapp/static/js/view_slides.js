    var mainSwiper = new Swiper('.main-swiper', {
        pagination: {
            el: '.swiper-pagination',
            type: 'fraction',
        },
        navigation: {
            nextEl: '.swiper-button-next',
            prevEl: '.swiper-button-prev',
        },
        loop: true,
        spaceBetween: 30,
        centeredSlides: true,
        breakpoints: {
            640: {
                slidesPerView: 1,
                spaceBetween: 20,
            },
            768: {
                slidesPerView: 1,
                spaceBetween: 40,
            },
            1024: {
                slidesPerView: 1,
                spaceBetween: 50,
            },
        }
    });

    var fullscreenSwiper;

    function enterFullscreen() {
        var fullscreenContainer = document.getElementById('fullscreen-container');
        if (fullscreenContainer.requestFullscreen) {
            fullscreenContainer.requestFullscreen();
        } else if (fullscreenContainer.mozRequestFullScreen) {      // Firefox
            fullscreenContainer.mozRequestFullScreen();
        } else if (fullscreenContainer.webkitRequestFullscreen) {   // Chrome, Safari, Opera
            fullscreenContainer.webkitRequestFullscreen();
        } else if (fullscreenContainer.msRequestFullscreen) {       // IE/Edge
            fullscreenContainer.msRequestFullscreen();
        }
        fullscreenContainer.style.display = 'flex';
        document.body.style.overflow = 'hidden';  // Disable scrolling on the main page

        // Initialize fullscreen swiper only when entering fullscreen
        if (!fullscreenSwiper) {
            fullscreenSwiper = new Swiper('.fullscreen-swiper', {
                pagination: {
                    el: '.swiper-pagination',
                    type: 'fraction',
                },
                navigation: {
                    nextEl: '.swiper-button-next',
                    prevEl: '.swiper-button-prev',
                },
                loop: true,
                spaceBetween: 30,
                centeredSlides: true,
                breakpoints: {
                    640: {
                        slidesPerView: 1,
                        spaceBetween: 20,
                    },
                    768: {
                        slidesPerView: 1,
                        spaceBetween: 40,
                    },
                    1024: {
                        slidesPerView: 1,
                        spaceBetween: 50,
                    },
                }
            });
        }
    }

    function exitFullscreen() {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        } else if (document.mozCancelFullScreen) {    // Firefox
            document.mozCancelFullScreen();
        } else if (document.webkitExitFullscreen) {   // Chrome, Safari, Opera
            document.webkitExitFullscreen();
        } else if (document.msExitFullscreen) {       // IE/Edge
            document.msExitFullscreen();
        }
        document.getElementById('fullscreen-container').style.display = 'none';
        document.body.style.overflow = 'auto';  // Enable scrolling on the main page
    }

    // Listen for fullscreen change events to handle the display of the fullscreen container
    document.addEventListener('fullscreenchange', function() {
        if (!document.fullscreenElement) {
            document.getElementById('fullscreen-container').style.display = 'none';
            document.body.style.overflow = 'auto';
        }
    });

    document.addEventListener('webkitfullscreenchange', function() {
        if (!document.webkitFullscreenElement) {
            document.getElementById('fullscreen-container').style.display = 'none';
            document.body.style.overflow = 'auto';
        }
    });

    document.addEventListener('mozfullscreenchange', function() {
        if (!document.mozFullScreenElement) {
            document.getElementById('fullscreen-container').style.display = 'none';
            document.body.style.overflow = 'auto';
        }
    });

    document.addEventListener('msfullscreenchange', function() {
        if (!document.msFullscreenElement) {
            document.getElementById('fullscreen-container').style.display = 'none';
            document.body.style.overflow = 'auto';
        }
    });
