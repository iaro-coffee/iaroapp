from allauth.account.models import EmailAddress
from allauth.account.utils import user_email
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.shortcuts import reverse


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """Hook that is called just before a user logs in via a social account."""
        if sociallogin.is_existing:
            # If the user exists, we check if the social account is connected, otherwise we connect it.
            return

        # Check if the email address already exists.
        try:
            email = user_email(sociallogin.user)
            email_address = EmailAddress.objects.get(email=email, verified=True)
            user = email_address.user

            # Connect the existing Django account with this social account
            sociallogin.connect(request, user)
        except EmailAddress.DoesNotExist:
            # If the email does not exist or is not verified, we proceed as normal.
            pass

    def get_login_redirect_url(self, request):
        """Specify the redirect URL after a successful social login."""
        return reverse("customer_index")
