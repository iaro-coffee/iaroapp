import json
import os

import requests
from dotenv import find_dotenv, load_dotenv
from requests.exceptions import HTTPError, RequestException, Timeout
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

load_dotenv(find_dotenv())


class Planday:
    auth_url = "https://id.planday.com/connect/token"
    base_url = "https://openapi.planday.com"
    client_id = os.environ["CLIENT_ID"]
    refresh_token = os.environ["REFRESH_TOKEN"]
    access_token = None
    session = requests.session()
    session.trust_env = False

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((RequestException, Timeout)),
    )
    def authenticate(self):
        """
        Authenticate with the Planday API using the refresh token. Retries on network-related
        issues and handles token expiration.
        """
        try:
            # Prepare the payload and headers for the authentication request
            payload = {
                "client_id": self.client_id,
                "refresh_token": self.refresh_token,
                "grant_type": "refresh_token",
            }
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "X-ClientId": self.client_id,
            }

            # Send the authentication request
            response = self.session.post(self.auth_url, headers=headers, data=payload)
            response.raise_for_status()

            # Parse the access token
            response_data = response.json()
            self.access_token = response_data.get("access_token")

            if not self.access_token:
                raise ValueError("Access token not found in the response.")

        except HTTPError as e:
            if e.response.status_code == 401:
                raise PermissionError(
                    "Invalid credentials. Please check your client ID and refresh token."
                )
            else:
                raise e  # Re-raise other HTTP errors for further handling
        except (RequestException, Timeout) as e:
            raise ConnectionError(f"Network error occurred: {e}")
        except ValueError as e:
            raise ValueError(f"Authentication failed: {e}")
        except Exception as e:
            # General fallback for any other unexpected errors
            raise RuntimeError(
                f"An unexpected error occurred during authentication: {e}"
            )

    def get_auth_headers(self):
        """
        Return headers with the authorization token. Calls authenticate if no token exists.
        """
        if not self.access_token:
            self.authenticate()

        return {
            "Authorization": f"Bearer {self.access_token}",
            "X-ClientId": self.client_id,
            "Content-Type": "application/json",
        }

    def get_portal_info(self):
        """
        Fetch the portal information from Planday API.
        """
        try:
            auth_headers = self.get_auth_headers()
            endpoint = "/portal/v1.0/info"
            url = f"{self.base_url}{endpoint}"

            response = self.session.get(url, headers=auth_headers)
            response.raise_for_status()

            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise PermissionError(
                    "Unauthorized access. Please check your credentials."
                )
            else:
                raise

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def get_employees(self):
        auth_headers = self.get_auth_headers()
        response = self.session.get(
            f"{self.base_url}/hr/v1/employees", headers=auth_headers
        )
        response.raise_for_status()

        try:
            response_json = response.json()
        except ValueError:
            raise ValueError("Invalid JSON response from Planday API")

        if "data" not in response_json:
            raise ValueError(f"Unexpected API response structure: {response_json}")

        employees = response_json["data"]
        if not all(isinstance(emp, dict) for emp in employees):
            raise ValueError(f"Unexpected employee data structure: {employees}")
        return employees

    def get_employee_id_by_email(self, email):
        employees = self.get_employees()
        for employee in employees:
            if isinstance(employee, dict) and employee.get("email") == email:
                return employee.get("id")
        return None

    def get_user_shifts(
        self, employee_id, from_date, to_date, limit=50, status="Assigned"
    ):
        """
        Fetch shifts for a specific employee within the provided date range.
        """
        auth_headers = self.get_auth_headers()
        payload = {
            "From": from_date,
            "To": to_date,
            "EmployeeId": [employee_id],
            "Limit": limit,
            "ShiftStatus": status,
        }

        response = self.session.get(
            f"{self.base_url}/scheduling/v1.0/shifts",
            headers=auth_headers,
            params=payload,
        )
        response.raise_for_status()

        try:
            response_data = response.json()

            if not isinstance(response_data, dict):
                raise ValueError(f"Unexpected response type: {type(response_data)}")

            shifts = response_data.get("data", [])

            if not isinstance(shifts, list):
                raise ValueError(f"Unexpected type for 'data' field: {type(shifts)}")

            return shifts

        except ValueError as e:
            raise ValueError(f"Invalid JSON response from Planday API: {e}")

    def punch_in_by_email(self, email):
        employeeId = self.get_employee_id_by_email(email)
        if employeeId is None:
            return 500
        auth_headers = {
            "Authorization": "Bearer " + self.access_token,
            "X-ClientId": self.client_id,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        payload = {"comment": ""}
        response = self.session.request(
            "POST",
            self.base_url
            + "/punchclock/v1/punchclockshifts/employee/"
            + str(employeeId)
            + "/punchin",
            headers=auth_headers,
            json=payload,
        )
        return response.status_code

    def punch_out_by_email(self, email):
        employeeId = self.get_employee_id_by_email(email)
        if employeeId is None:
            return 500
        auth_headers = {
            "Authorization": "Bearer " + self.access_token,
            "X-ClientId": self.client_id,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        payload = {
            "comment": "",
        }
        response = self.session.request(
            "PUT",
            self.base_url
            + "/punchclock/v1/punchclockshifts/employee/"
            + str(employeeId)
            + "/punchout",
            headers=auth_headers,
            json=payload,
        )
        return response.status_code

    def get_employee_group_name(self, group_id):
        auth_headers = {
            "Authorization": "Bearer " + self.access_token,
            "X-ClientId": self.client_id,
        }
        response = self.session.request(
            "GET",
            self.base_url + "/hr/v1/employeegroups/" + str(group_id),
            headers=auth_headers,
        )
        response = json.loads(response.text)
        response = response["data"]
        return response["name"]

    def get_user_groups(self, employeeId):
        auth_headers = {
            "Authorization": "Bearer " + self.access_token,
            "X-ClientId": self.client_id,
        }
        response = self.session.request(
            "GET",
            self.base_url + "/hr/v1/employees/" + str(employeeId),
            headers=auth_headers,
        )
        response = json.loads(response.text)
        return response["data"]["employeeGroups"]

    def get_user_punchclock_records_of_timespan(self, employeeEmail, fromDate, toDate):
        employeeId = self.get_employee_id_by_email(employeeEmail)
        auth_headers = {
            "Authorization": "Bearer " + self.access_token,
            "X-ClientId": self.client_id,
        }

        fromStart = fromDate.strftime("%Y-%m-%dT00:00")
        toEnd = toDate.strftime("%Y-%m-%dT23:59")

        payload = {
            "employeeId": employeeId,
            "from": fromStart,
            "to": toEnd,
        }

        response = self.session.request(
            "GET",
            self.base_url + "/punchclock/v1/punchclockshifts",
            headers=auth_headers,
            params=payload,
        )
        response = json.loads(response.text)
        response = response["data"]

        return response

    def get_departments(self, limit=50, offset=0):
        """Fetches the list of departments from the Planday API."""
        auth_headers = {
            "Authorization": "Bearer " + self.access_token,
            "X-ClientId": self.client_id,
        }

        params = {
            "limit": limit,
            "offset": offset,
        }

        response = self.session.get(
            f"{self.base_url}/hr/v1.0/departments", headers=auth_headers, params=params
        )

        if response.status_code == 200:
            try:
                data = response.json()
                departments = data.get("data", [])
                return departments
            except json.JSONDecodeError:
                print("Error decoding JSON response.")
                return []
        else:
            print(f"Failed to fetch departments. Status code: {response.status_code}")
            return []

    def get_employee_groups(self, limit=50, offset=0):
        """Fetches the list of employee groups from the Planday API."""
        auth_headers = {
            "Authorization": "Bearer " + self.access_token,
            "X-ClientId": self.client_id,
        }

        params = {
            "limit": limit,
            "offset": offset,
        }

        response = self.session.get(
            f"{self.base_url}/hr/v1.0/employeegroups",
            headers=auth_headers,
            params=params,
        )

        if response.status_code == 200:
            try:
                data = response.json()
                employee_groups = data.get("data", [])
                return employee_groups
            except json.JSONDecodeError:
                print("Error decoding JSON response.")
                return []
        else:
            print(
                f"Failed to fetch employee groups. Status code: {response.status_code}"
            )
            return []


"""
  ## response example
{'paging': {'offset': 0, 'limit': 50, 'total': 40}, 'data':
[{'securityGroups': [],
'id': 1186664,
'dateTimeCreated': '2024-03-18',
'dateTimeModified': '2024-05-20T18:55:11.967Z',
'employeeTypeId': 112483,
'salaryIdentifier': '1196664',
'firstName': 'Zuzana',
'lastName': 'Svantnerova',
'userName': 'zuzana.svantnerova@gmail.com',
'cellPhone': '+49',
'phone': '',
'email': 'zuzana.svantnerova@gmail.com',
'departments': [154388],
'employeeGroups': [274170],
'cellPhoneCountryPrefix': '+49',
'cellPhoneCountryCode': 'DE'}]}
"""
