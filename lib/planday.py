import datetime
import json
import os

import requests
from dateutil.relativedelta import relativedelta
from django.core.cache import cache
from dotenv import find_dotenv, load_dotenv
from requests.exceptions import RequestException, Timeout
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
        Authenticate with the Planday API using the refresh token. Caches the access token
        for reuse. Retries on network-related issues and handles token expiration.
        """
        try:
            # Check cache for existing access token
            access_token = cache.get("planday_access_token")
            if access_token:
                self.access_token = access_token
                return

            # Prepare the payload and headers for the authentication request
            payload = {
                "client_id": self.client_id,
                "refresh_token": self.refresh_token,
                "grant_type": "refresh_token",
            }
            headers = {"Content-Type": "application/x-www-form-urlencoded"}

            # Send the authentication request
            response = self.session.post(self.auth_url, headers=headers, data=payload)
            response.raise_for_status()

            # Parse and cache the access token
            response_data = response.json()
            self.access_token = response_data.get("access_token")
            expires_in = response_data.get(
                "expires_in", 3600
            )  # Default to 1 hour if not provided

            # Cache the access token
            if self.access_token:
                cache.set("planday_access_token", self.access_token, timeout=expires_in)
            else:
                raise ValueError("Access token not found in the response.")

        except requests.HTTPError as e:
            if e.response.status_code == 401:
                # 401 Unauthorized, possibly due to invalid credentials
                cache.delete("planday_access_token")
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
        Return headers with the authorization token.
        """
        if not self.access_token:
            self.authenticate()

        return {
            "Authorization": f"Bearer {self.access_token}",
            "X-ClientId": self.client_id,
            "Content-Type": "application/json",
        }

    def get_portal_info(self):
        """Fetch the portal information"""
        auth_headers = {
            "Authorization": f"Bearer {self.access_token}",
            "X-ClientId": self.client_id,
        }
        endpoint = "/portal/v1.0/info"
        url = f"{self.base_url}{endpoint}"

        response = self.session.get(url, headers=auth_headers)
        response.raise_for_status()

        return response.json()

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

    def get_employee_id_by_email(self, email):
        employees = self.get_employees()
        for key, value in employees.items():
            if value["email"] == email:
                return value["id"]
        return None

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def get_employees(self):
        auth_headers = {
            "Authorization": "Bearer " + self.access_token,
            "X-ClientId": self.client_id,
        }
        response = self.session.request(
            "GET", self.base_url + "/hr/v1/employees", headers=auth_headers
        )

        try:
            response_json = response.json()
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON response from Planday API")

        if "data" not in response_json:
            print(f"Unexpected API response: {response_json}")
            return {}

        employees = {employee["id"]: employee for employee in response_json["data"]}
        return employees

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

    def get_user_shifts_of_day(self, day):
        employees = self.get_employees()
        auth_headers = {
            "Authorization": "Bearer " + self.access_token,
            "X-ClientId": self.client_id,
        }
        todayStart = day.strftime("%Y-%m-%dT00:00")
        todayEnd = day.strftime("%Y-%m-%dT23:59")

        payload = {
            "from": todayStart,
            "to": todayEnd,
        }

        response = self.session.request(
            "GET",
            self.base_url + "/punchclock/v1/punchclockshifts",
            headers=auth_headers,
            params=payload,
        )
        response = json.loads(response.text)
        response = response["data"]
        user_shifts = {}
        for shift in response:
            if "employeeId" in shift:
                user_shifts[employees[shift["employeeId"]]["email"]] = shift
        return user_shifts

    def get_upcoming_shifts_for_user(self, user_email):
        # Ensure the user is authenticated before making the request
        self.authenticate()  # This will cache the token and only authenticate if necessary

        employeeId = self.get_employee_id_by_email(user_email)
        if employeeId is None:
            return []

        auth_headers = {
            "Authorization": f"Bearer {self.access_token}",
            "X-ClientId": self.client_id,
        }
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        nextMonth = (datetime.datetime.now() + relativedelta(months=1)).strftime(
            "%Y-%m-%d"
        )

        payload = {
            "from": today,
            "to": nextMonth,
            "limit": 5000,
            "employeeId": employeeId,
        }

        response = self.session.get(
            f"{self.base_url}/scheduling/v1/shifts",
            headers=auth_headers,
            params=payload,
        )

        try:
            response.raise_for_status()  # Raise an exception for HTTP errors
            data = response.json()
        except (requests.HTTPError, json.JSONDecodeError) as e:
            print(f"Error fetching shifts for {user_email}: {e}")
            return []

        shifts = []

        for shift in data.get("data", []):
            start = shift["startDateTime"]
            end = shift["endDateTime"]
            departmentId = shift.get("departmentId", "")
            groupId = shift.get("employeeGroupId", "")
            comment = shift.get("comment", "")

            shifts.append(
                {
                    "start": start,
                    "end": end,
                    "departmentId": departmentId,
                    "groupId": groupId,
                    "comment": comment,
                }
            )

        return shifts

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
                for department in departments:
                    print(
                        f"Department ID: {department['id']}, Name: {department['name']}"
                    )
                return departments
            except json.JSONDecodeError:
                print("Error decoding JSON response.")
                return []
        else:
            print(f"Failed to fetch departments. Status code: {response.status_code}")
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
