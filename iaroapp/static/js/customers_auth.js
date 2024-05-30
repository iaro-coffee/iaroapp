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

        localStorage.setItem('formState', state);
    }

    document.getElementById('show-signup').addEventListener('click', function (e) {
        e.preventDefault();
        switchToForm('signup');
    });

    document.getElementById('show-login').addEventListener('click', function (e) {
        e.preventDefault();
        switchToForm('login');
    });

    function getQueryParameter(name) {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get(name);
    }
    const queryFormState = getQueryParameter('form');
    const formState = queryFormState || localStorage.getItem('formState') || 'login';
    switchToForm(formState);



    // handle help text for register form
    const fields = [
        {input: document.getElementById('id_signup_email'),
            helpText: document.getElementById('help_email')},
        {input: document.getElementById('id_signup_password1'),
            helpText: document.getElementById('help_password1')}
    ];

    fields.forEach(field => {
        field.input.addEventListener('focus', function () {
            // console.log('Focus event fired');
            field.helpText.classList.remove('hidden_text');
            field.helpText.classList.add('visible_text');
        });

        field.input.addEventListener('blur', function () {
            field.helpText.classList.remove('visible_text');
            field.helpText.classList.add('hidden_text');
        });
    });



    // handle field and non-field errors for register form
    document.getElementById('signup-form').addEventListener('submit', function (event) {
        event.preventDefault();
        let errorContainer = document.getElementById('form-errors');
        let form = event.target;
        let formData = new FormData(form);
        let csrfToken = formData.get('csrfmiddlewaretoken');
        let urlData = document.getElementById('urls');
        let registerUrl = urlData.dataset.registerUrl;
        let indexUrl = urlData.dataset.indexUrl;

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

                    window.location.href = indexUrl;
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
    });
});

