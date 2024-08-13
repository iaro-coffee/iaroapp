import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()

DEFAULT_TIMEOUT = 30


def generate_access_token():
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
        return response_data["access_token"]
    else:
        raise Exception(f"Error generating access token: {response_data}")


def get_template_details(template_id, oauth_token):
    headers = {"Authorization": f"Zoho-oauthtoken {oauth_token}"}
    url = f"https://sign.zoho.eu/api/v1/templates/{template_id}"

    response = requests.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error getting template details: {response.json()}")


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
    data_json = {"data": json.dumps(data), "is_quicksend": True}

    url = f"https://sign.zoho.eu/api/v1/templates/{template_id}/createdocument"
    response = requests.post(
        url, data=data_json, headers=headers, timeout=DEFAULT_TIMEOUT
    )

    if response.status_code == 200:
        print("Success! Here is the response:")
        print("Response Status Code:", response.status_code)
        print("Response Headers:", json.dumps(dict(response.headers), indent=4))

        response_json = response.json()
        print("Response Content:", json.dumps(response_json, indent=4))

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
        return response.json().get("signing_url")
    else:
        raise Exception(f"Error getting signing URL: {response.json()}")


template_id = "66746000000038081"
oauth_token = generate_access_token()
recipient_email = "3dom.ua@gmail.com"
recipient_name = "John Doe"
send_document_using_template(
    template_id,
    get_template_details(template_id, oauth_token),
    recipient_email,
    recipient_name,
    oauth_token,
)
