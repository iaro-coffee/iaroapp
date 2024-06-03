document.addEventListener("DOMContentLoaded", function () {
    const card = document.querySelector('.card');
    const cardContent = document.querySelector('.card-content');
    const header = document.querySelector('h6.text-center');
    const logo = document.querySelector('.logo-container');


    // handle displaying and switching login/signup forms
    function switchToForm(state) {
        const isSignup = state === 'signup';
        card.classList.toggle('rotate-to-signup', isSignup);
        card.classList.toggle('rotate-to-login', !isSignup);
        cardContent.classList.add('blur-effect');
        logo.classList.add('blur-effect');

        setTimeout(function () {
            cardContent.style.transform = `rotateY(${isSignup ? '180deg' : '0deg'})`;
            logo.style.transform = `rotateY(${isSignup ? '180deg' : '0deg'})`;

            document.getElementById('signup-form').classList.toggle('hidden', !isSignup);
            document.getElementById('signup-form').classList.toggle('visible', isSignup);
            document.getElementById('login-form').classList.toggle('hidden', isSignup);
            document.getElementById('login-form').classList.toggle('visible', !isSignup);

            cardContent.classList.remove('blur-effect');
            logo.classList.remove('blur-effect');
            header.textContent = isSignup ? 'Register' : 'Log In';
        }, 300);
    }

    document.getElementById('show-signup').addEventListener('click', function (e) {
        e.preventDefault();
        switchToForm('signup');
    });

    document.getElementById('show-login').addEventListener('click', function (e) {
        e.preventDefault();
        switchToForm('login');
    });


    // handle help text for register form
    const fields = [
        {
            input: document.getElementById('id_signup_email'),
            helpText: document.getElementById('help_email')
        },
        {
            input: document.getElementById('id_signup_password1'),
            helpText: document.getElementById('help_password1')
        }
    ];

    fields.forEach(field => {
        field.input.addEventListener('focus', function () {
            field.helpText.classList.remove('hidden_text');
            field.helpText.classList.add('visible_text');
        });

        field.input.addEventListener('blur', function () {
            field.helpText.classList.remove('visible_text');
            field.helpText.classList.add('hidden_text');
        });
    });


    // handle register form errors
    document.getElementById('signup-form').addEventListener('submit', function (event) {
        event.preventDefault();
        let errorContainer = document.getElementById('form-signup-errors');
        let form = event.target;
        let formData = new FormData(form);
        let csrfToken = formData.get('csrfmiddlewaretoken');
        let urlData = document.getElementById('urls');
        let registerUrl = urlData.dataset.registerUrl;
        let confimUrl = urlData.dataset.indexUrl;

        fetch(registerUrl, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
            },
            body: formData,
        })
            .then(response => response.json())
            .then(data => {
                if (!data.success) {
                    errorContainer.classList.remove('hidden_text');
                    errorContainer.classList.add('visible_text');
                    let errors = JSON.parse(data.errors);
                    let errorHtml = '<ul class="mb-0">';
                    for (let key in errors) {
                        if (errors.hasOwnProperty(key)) {
                            errors[key].forEach(error => {
                                errorHtml += `<li>${error.message}</li>`;
                            });
                        }
                    }
                    errorHtml += '</ul>';
                    errorContainer.innerHTML = errorHtml;
                } else {
                    errorContainer.classList.remove('visible_text');
                    errorContainer.classList.add('hidden_text');

                    window.location.href = confimUrl;
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
    });

    // handle login form errors
    document.getElementById('login-form').addEventListener('submit', function (event) {
        event.preventDefault();
        let errorContainer = document.getElementById('form-login-errors');
        let form = event.target;
        let formData = new FormData(form);
        let csrfToken = formData.get('csrfmiddlewaretoken');
        let loginUrl = form.action;

        fetch(loginUrl, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
            },
            body: formData,
        })
            .then(response => response.json())
            .then(data => {
                if (!data.success) {
                    errorContainer.classList.remove('hidden_text');
                    errorContainer.classList.add('visible_text');
                    let errors = JSON.parse(data.errors);
                    let errorHtml = '<ul class="mb-0">';
                    for (let key in errors) {
                        if (errors.hasOwnProperty(key)) {
                            errors[key].forEach(error => {
                                errorHtml += `<li>${error.message}</li>`;
                            });
                        }
                    }
                    errorHtml += '</ul>';
                    errorContainer.innerHTML = errorHtml;
                } else {
                    errorContainer.classList.add('hidden_text');
                    errorContainer.classList.remove('visible_text');
                    window.location.href = data.redirectUrl;
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
    });


});
