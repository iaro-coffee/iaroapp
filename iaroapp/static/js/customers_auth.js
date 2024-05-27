document.addEventListener("DOMContentLoaded", function () {
    const card = document.querySelector('.card');
    const cardContent = document.querySelector('.card-content');
    const header = document.querySelector('h6.text-center');
    const logo = document.querySelector('.logo-container');

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

    const formState = localStorage.getItem('formState') || 'login';
    switchToForm(formState);

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
