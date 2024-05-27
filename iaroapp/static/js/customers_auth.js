document.getElementById('show-signup').addEventListener('click', function (e) {
    e.preventDefault();
    const card = document.querySelector('.card');
    const cardContent = document.querySelector('.card-content');
    const header = document.querySelector('h6.text-center');
    const logo = document.querySelector('.logo-container');

    card.classList.add('rotate-to-signup');
    card.classList.remove('rotate-to-login');
    cardContent.classList.add('blur-effect');

    setTimeout(function () {
        cardContent.style.transform = 'rotateY(180deg)';
        logo.style.transform = 'rotateY(180deg)';

        document.getElementById('login-form').classList.remove('visible');
        document.getElementById('login-form').classList.add('hidden');
        document.getElementById('signup-form').classList.remove('hidden');
        document.getElementById('signup-form').classList.add('visible');
        cardContent.classList.remove('blur-effect');
        header.textContent = 'Register';
    }, 300);

    localStorage.setItem('formState', 'signup');
});

document.getElementById('show-login').addEventListener('click', function (e) {
    e.preventDefault();
    const card = document.querySelector('.card');
    const cardContent = document.querySelector('.card-content');
    const header = document.querySelector('h6.text-center');
    const logo = document.querySelector('.logo-container');

    card.classList.add('rotate-to-login');
    card.classList.remove('rotate-to-signup');
    cardContent.classList.add('blur-effect');

    setTimeout(function () {
        cardContent.style.transform = 'rotateY(0deg)';
        logo.style.transform = 'rotateY(0deg)';

        document.getElementById('signup-form').classList.remove('visible');
        document.getElementById('signup-form').classList.add('hidden');
        document.getElementById('login-form').classList.remove('hidden');
        document.getElementById('login-form').classList.add('visible');
        cardContent.classList.remove('blur-effect');
        header.textContent = 'Log In';
    }, 300);

    localStorage.setItem('formState', 'login');
});

document.addEventListener("DOMContentLoaded", function () {
    const formState = localStorage.getItem('formState');
    const card = document.querySelector('.card');
    const header = document.querySelector('h6.text-center');
    const logo = document.querySelector('.logo-container');

    if (formState === 'signup') {
        card.classList.add('rotate-to-signup');
        card.classList.remove('rotate-to-login');
        document.getElementById('login-form').classList.remove('visible');
        document.getElementById('login-form').classList.add('hidden');

        setTimeout(function () {
            document.querySelector('.card-content').style.transform = 'rotateY(180deg)';
            logo.style.transform = 'rotateY(180deg)';
            document.getElementById('signup-form').classList.remove('hidden');
            document.getElementById('signup-form').classList.add('visible');
            header.textContent = 'Register';
        }, 300);
    } else {
        card.classList.add('rotate-to-login');
        card.classList.remove('rotate-to-signup');
        document.getElementById('signup-form').classList.remove('visible');
        document.getElementById('signup-form').classList.add('hidden');

        setTimeout(function () {
            document.querySelector('.card-content').style.transform = 'rotateY(0deg)';
            logo.style.transform = 'rotateY(0deg)';
            document.getElementById('login-form').classList.remove('hidden');
            document.getElementById('login-form').classList.add('visible');
            header.textContent = 'Log In';
        }, 300);
    }
});

document.addEventListener("DOMContentLoaded", function () {
    const fields = [
        {input: document.getElementById('id_signup_username'), helpText: document.getElementById('help_username')},
        {input: document.getElementById('id_signup_email'), helpText: document.getElementById('help_email')},
        {input: document.getElementById('id_signup_password1'), helpText: document.getElementById('help_password1')}
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
});
