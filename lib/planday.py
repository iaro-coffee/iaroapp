import requests
import json
from dotenv import load_dotenv, find_dotenv
import os
import datetime
from dateutil.relativedelta import relativedelta

load_dotenv(find_dotenv())

class Planday:
  auth_url = 'https://id.planday.com/connect/token'
  base_url = 'https://openapi.planday.com'
  client_id = os.environ['CLIENT_ID']
  refresh_token = os.environ['REFRESH_TOKEN']
  access_token = ''
  session = requests.session()
  session.trust_env = False

  def authenticate(self):
    payload = {
      'client_id': self.client_id,
      'refresh_token': self.refresh_token,
      'grant_type': 'refresh_token'
    }
    headers = {
      'Content-Type': 'application/x-www-form-urlencoded'
    }
    response = self.session.request("POST", self.auth_url, headers=headers, data=payload)
    response = json.loads(response.text)
    self.access_token = response['access_token']

  def get_employees(self):  
    auth_headers = {
      'Authorization': 'Bearer ' + self.access_token,
      'X-ClientId': self.client_id
    }
    response = self.session.request("GET", self.base_url + '/hr/v1/employees', headers=auth_headers)
    response = json.loads(response.text)
    response = response['data']
    employees = {}
    for employee in response:
      employees[employee['id']] = employee
    return employees

  def get_employee_group_name(self, group_id):
    auth_headers = {
      'Authorization': 'Bearer ' + self.access_token,
      'X-ClientId': self.client_id
    }
    response = self.session.request("GET", self.base_url + '/hr/v1/employeegroups/' + str(group_id), headers=auth_headers)
    response = json.loads(response.text)
    response = response['data']
    return response['name']

  def get_user_groups(self, employeeId):
    auth_headers = {
      'Authorization': 'Bearer ' + self.access_token,
      'X-ClientId': self.client_id
    }
    response = self.session.request("GET", self.base_url + '/hr/v1/employees/' + str(employeeId), headers=auth_headers)
    response = json.loads(response.text)
    return response['data']['employeeGroups']


  def get_user_shifts_of_day(self, day):
    employees = self.get_employees()
    auth_headers = {
      'Authorization': 'Bearer ' + self.access_token,
      'X-ClientId': self.client_id
    }
    todayStart = day.strftime("%Y-%m-%dT00:00")
    todayEnd = day.strftime("%Y-%m-%dT23:59")

    payload = {
      'from': todayStart,
      'to': todayEnd,
    }

    response = self.session.request("GET", self.base_url + '/punchclock/v1/punchclockshifts', headers=auth_headers, params=payload)
    response = json.loads(response.text)
    #print(response)
    response = response['data']
    user_shifts = {}
    for shift in response:
      if 'employeeId' in shift:
        user_shifts[employees[shift['employeeId']]['email']] = shift
    return user_shifts

  def get_upcoming_shifts(self,starting , until):
    employees = self.get_employees()
    auth_headers = {
      'Authorization': 'Bearer ' + self.access_token,
      'X-ClientId': self.client_id
    }
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    nextMonth = (datetime.datetime.now() + relativedelta(months=1)).strftime("%Y-%m-%d")
    payload = {
      'from': today if starting is None else starting,
      'to': nextMonth if until is None else until,
      'limit': 5000,
    }
    response = self.session.request("GET", self.base_url + '/scheduling/v1/shifts', headers=auth_headers, params=payload)
    response = json.loads(response.text)
    response = response['data']
    shifts = []
    for shift in response:
      if 'employeeId' in shift:
        employee = employees[shift['employeeId']]['email']
        employeeId = shift['employeeId']
        start = shift['startDateTime']
        end = shift['endDateTime']
        departmentId = shift['departmentId']
        groupId = shift['employeeGroupId']
        shifts.append({"employee": employee, "employeeId": employeeId, "departmentId":departmentId, "groupId": groupId, "start": start, "end": end})
    return shifts