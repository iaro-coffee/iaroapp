import json
import os

import requests
from django.core.cache import cache
from dotenv import load_dotenv

load_dotenv()

DEFAULT_TIMEOUT = 30
ZOHO_TOKEN_CACHE_KEY = "zoho_access_token"  # nosec
ZOHO_TOKEN_EXPIRY = 3600


def generate_access_token():
    access_token = cache.get(ZOHO_TOKEN_CACHE_KEY)

    if not access_token:
        url = "https://accounts.zoho.eu/oauth/v2/token"
        data = {
            "refresh_token": os.environ.get("ZOHO_REFRESH_TOKEN"),
            "client_id": os.environ.get("ZOHO_CLIENT_ID"),
            "client_secret": os.environ.get("ZOHO_CLIENT_SECRET"),
            "redirect_uri": os.environ.get("ZOHO_REDIRECT_URI"),
            "grant_type": "refresh_token",
        }

        response = requests.post(url, data=data, timeout=DEFAULT_TIMEOUT)
        response_data = response.json()

        if response.status_code == 200:
            access_token = response_data["access_token"]
            cache.set(ZOHO_TOKEN_CACHE_KEY, access_token, ZOHO_TOKEN_EXPIRY)
        elif response.status_code == 401:
            # Token creation throttle limit reached or token is expired, attempt to get a new token
            cache.delete(ZOHO_TOKEN_CACHE_KEY)
            response = requests.post(url, data=data, timeout=DEFAULT_TIMEOUT)
            response_data = response.json()

            if response.status_code == 200:
                access_token = response_data["access_token"]
                cache.set(ZOHO_TOKEN_CACHE_KEY, access_token, ZOHO_TOKEN_EXPIRY)
            else:
                raise Exception(
                    f"Error generating access token on retry: {response_data}"
                )
        else:
            raise Exception(f"Error generating access token: {response_data}")

    return access_token


def get_template_details(template_id, oauth_token):
    headers = {"Authorization": f"Zoho-oauthtoken {oauth_token}"}
    url = f"https://sign.zoho.eu/api/v1/templates/{template_id}"

    response = requests.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)

    if response.status_code == 200:
        # print(response.json())
        return response.json()
    else:
        raise Exception(f"Error getting template details: {response.json()}")


# get_template_details(66746000000038081, generate_access_token())


def send_document_using_template(
    template_id, template_details, recipient_email, recipient_name, oauth_token
):
    headers = {"Authorization": f"Zoho-oauthtoken {oauth_token}"}

    temp_data = {}
    actions = template_details["templates"]["actions"]
    new_action_array = []

    for action in actions:
        new_action = {
            "recipient_email": recipient_email,
            "recipient_name": recipient_name,
            "action_id": action["action_id"],
            "action_type": "SIGN",  # Standard action type for signing
            "private_notes": "",
            "signing_order": action["signing_order"],
            "role": action.get("role"),  # Pass the role if applicable
            "verify_recipient": False,  # Set to True if you want to verify the recipient's identity
            "is_embedded": True,  # This makes the action embedded
        }
        new_action_array.append(new_action)

    temp_data["actions"] = new_action_array

    data = {"templates": temp_data}
    data_json = {"data": json.dumps(data), "is_quicksend": True, "testing": True}

    url = f"https://sign.zoho.eu/api/v1/templates/{template_id}/createdocument"
    response = requests.post(
        url, data=data_json, headers=headers, timeout=DEFAULT_TIMEOUT
    )

    if response.status_code == 200:

        response_json = response.json()
        print("Response Content Received")

        # Extract request_id and action_id
        request_id = response_json.get("requests", {}).get("request_id")

        actions = response_json.get("requests", {}).get("actions", [])
        if not actions:
            print("No actions found in the response.")
            raise ValueError("No actions found in the response.")

        action_id = actions[0].get("action_id")

        # Debugging: Print the request_id and action_id to inspect them
        print(f"Extracted Request ID: {request_id}, Action ID: {action_id}")

        if not request_id or not action_id:
            raise ValueError("request_id or action_id is None, cannot proceed.")

        # Return the entire response JSON and the extracted IDs for further use
        return {
            "response_json": response_json,
            "request_id": request_id,
            "action_id": action_id,
        }
    else:
        raise Exception(f"Error sending document: {response.json()}")


def get_embedded_signing_url(request_id, action_id, domain_name, oauth_token):
    headers = {
        "Authorization": f"Zoho-oauthtoken {oauth_token}",
        "Content-Type": "application/json",
    }

    if not domain_name.startswith("https://"):
        domain_name = "https://" + domain_name

    url = f"https://sign.zoho.eu/api/v1/requests/{request_id}/actions/{action_id}/embedtoken?host={domain_name}"

    response = requests.post(url, headers=headers, timeout=DEFAULT_TIMEOUT)

    if response.status_code == 200:
        signing_url = response.json().get("sign_url")
        if not signing_url:
            raise Exception(
                f"Error: No signing_url returned by Zoho. Full response: {response.json()}"
            )
        return signing_url
    else:
        raise Exception(f"Error getting signing URL: {response.json()}")


def check_document_status(request_id, access_token):
    try:
        url = f"https://sign.zoho.eu/api/v1/requests/{request_id}"
        headers = {
            "Authorization": f"Zoho-oauthtoken {access_token}",
        }
        response = requests.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)

        if response.status_code == 200:
            data = response.json()
            request_status = data.get("requests", {}).get("request_status")
            print(request_status)
            return request_status
        else:
            print(f"Failed to get document status: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error checking document status: {str(e)}")
        return None


# check_document_status(66746000000043413, generate_access_token())
# get_embedded_signing_url(66746000000043235, 66746000000038106, "e91d-2a00-20-3042-c478-d6a0-f1b2-c005-e5ed.ngrok-free.app", generate_access_token())
