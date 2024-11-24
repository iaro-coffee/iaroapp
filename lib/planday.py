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


# Decorator to handle re-authentication on 401 errors
def planday_api_call(func):
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                # Token expired, re-authenticate and retry once
                self.access_token = None
                self.authenticate()
                return func(self, *args, **kwargs)
            else:
                raise

    return wrapper


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

    @planday_api_call
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

    @planday_api_call
    def get_employee_id_by_email(self, email):
        employees = self.get_employees()
        for employee in employees:
            if isinstance(employee, dict) and employee.get("email") == email:
                return employee.get("id")
        return None

    @planday_api_call
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

    @planday_api_call
    def get_shift_by_id(self, shift_id):
        """
        Fetch a shift by its ID from Planday.
        """
        version = "v1.0"
        auth_headers = self.get_auth_headers()
        endpoint = f"/scheduling/{version}/shifts/{shift_id}"
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.get(url, headers=auth_headers)
            response.raise_for_status()
            response_data = response.json()
            shift = response_data.get("data", {})
            return shift
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred while fetching shift by ID: {http_err}")
            # Log the response content for debugging
            print(f"Response content: {response.text}")
            return None
        except requests.exceptions.RequestException as req_err:
            print(f"Request exception occurred while fetching shift by ID: {req_err}")
            return None
        except ValueError as json_err:
            print(f"JSON decode error occurred: {json_err}")
            return None

    @planday_api_call
    def punch_in_by_email(self, email, shift_id=None, comment=""):
        print(f"Attempting punch-in for email: {email}")
        employeeId = self.get_employee_id_by_email(email)

        if employeeId is None:
            print("Error: No employee ID found for the given email.")
            return 500

        auth_headers = self.get_auth_headers()
        payload = {"comment": comment}
        if shift_id:
            payload["shiftId"] = shift_id  # Include shiftId in the payload

        # Print the payload to verify the comment
        print(f"Payload to Planday API: {payload}")

        try:
            version = "v1.0"

            url = (
                self.base_url
                + "/punchclock/"
                + version
                + "/punchclockshifts/employee/"
                + str(employeeId)
                + "/punchin"
            )

            # Print the full URL and payload for debugging
            print(f"Punch-In URL: {url}")
            print(f"Payload: {payload}")

            response = self.session.post(
                url,
                headers=auth_headers,
                json=payload,
            )
            print(f"Punch-In API response: {response.status_code} - {response.text}")
            return response.status_code
        except Exception as e:
            print(f"Exception during punch-in: {str(e)}")
            return 500

    @planday_api_call
    def punch_out_by_email(self, email, shift_id=None, comment=""):
        employeeId = self.get_employee_id_by_email(email)
        if employeeId is None:
            print("Failed to retrieve Employee ID for punch-out.")
            return None  # Properly handle if employeeId is not found

        auth_headers = self.get_auth_headers()
        payload = {"comment": comment}
        if shift_id:
            payload["shiftId"] = shift_id  # Include shiftId in the payload

        try:
            version = "v1.0"  # Use the correct API version

            url = (
                self.base_url
                + "/punchclock/"
                + version
                + "/punchclockshifts/employee/"
                + str(employeeId)
                + "/punchout"
            )

            # Print the full URL and payload for debugging
            print(f"Punch-Out URL: {url}")
            print(f"Payload: {payload}")

            response = self.session.put(
                url,
                headers=auth_headers,
                json=payload,
            )
            print(f"Punch-Out API response: {response.status_code} - {response.text}")
            return response  # Return the full response object
        except Exception as e:
            print(f"Exception during punch-out: {str(e)}")
            return None

    @planday_api_call
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

    @planday_api_call
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

    @planday_api_call
    def get_user_punchclock_records_of_timespan(self, employeeEmail, fromDate, toDate):
        employeeId = self.get_employee_id_by_email(employeeEmail)
        if not employeeId:
            raise ValueError("Invalid employee email provided.")

        auth_headers = {
            "Authorization": f"Bearer {self.access_token}",
            "X-ClientId": self.client_id,
        }

        fromStart = fromDate.strftime("%Y-%m-%dT00:00")
        toEnd = toDate.strftime("%Y-%m-%dT23:59")

        params = {
            "employeeId": employeeId,
            "from": fromStart,
            "to": toEnd,
        }

        url = f"{self.base_url}/punchclock/v1/punchclockshifts"

        try:
            response = self.session.get(
                url,
                headers=auth_headers,
                params=params,
                timeout=10,  # Timeout after 10 seconds
            )
            response.raise_for_status()  # Raise an exception for HTTP errors
        except Timeout:
            raise
        except HTTPError:
            raise
        except RequestException:
            raise

        try:
            data = response.json()
        except ValueError:
            raise

        punch_clock_records = data.get("data", [])

        return punch_clock_records

    @planday_api_call
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

    @planday_api_call
    def get_employee_groups(self, limit=50, offset=0):
        """Fetches the list of employee groups from the Planday API."""
        auth_headers = self.get_auth_headers()

        params = {
            "limit": limit,
            "offset": offset,
        }

        try:
            response = self.session.get(
                f"{self.base_url}/hr/v1.0/employeegroups",
                headers=auth_headers,
                params=params,
                timeout=10,  # Set a timeout of 10 seconds
            )
            response.raise_for_status()
        except requests.exceptions.Timeout:
            print("Request timed out while fetching employee groups.")
            return []
        except requests.exceptions.ConnectionError as e:
            print(f"Connection error occurred: {e}")
            return []
        except requests.exceptions.HTTPError as e:
            print(f"HTTP error occurred: {e}")
            if e.response.status_code == 401:
                # Token might have expired; re-authenticate
                self.access_token = None  # Reset the token
                return self.get_employee_groups(limit, offset)
            return []
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
            return []

        # Process the response if no exceptions occurred
        try:
            data = response.json()
            employee_groups = data.get("data", [])
            return employee_groups
        except json.JSONDecodeError:
            print("Error decoding JSON response.")
            return []

    @planday_api_call
    def get_user_shifts_bulk(self, employee_ids, from_date, to_date, limit=500):
        """
        Fetch shifts for multiple employees within the provided date range.
        """
        auth_headers = self.get_auth_headers()
        employee_ids_str = ",".join(map(str, employee_ids))

        payload = {
            "From": from_date,
            "To": to_date,
            "EmployeeId": employee_ids_str,
            "Limit": str(limit),
            "ShiftStatus": "Assigned",
        }

        response = self.session.get(
            f"{self.base_url}/scheduling/v1.0/shifts",
            headers=auth_headers,
            params=payload,
        )
        response.raise_for_status()

        try:
            response_data = response.json()
            shifts = response_data.get("data", [])
            return shifts
        except ValueError as e:
            raise ValueError(f"Invalid JSON response from Planday API: {e}")


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
