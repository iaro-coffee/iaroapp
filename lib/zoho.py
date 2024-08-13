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
        print(f"Access Token Generated: {response_data['access_token']}")
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
            "action_type": action["action_type"],
            "private_notes": "",
            "signing_order": action["signing_order"],
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
        return response.json()
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
