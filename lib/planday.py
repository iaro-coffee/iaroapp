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
      employees[employee['id']] = employee['email']
    return employees

  def get_shifts_today_users(self):
    employees = self.get_employees()
    auth_headers = {
      'Authorization': 'Bearer ' + self.access_token,
      'X-ClientId': self.client_id
    }
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    payload = {
      'from': today,
      'to': today
    }
    response = self.session.request("GET", self.base_url + '/scheduling/v1/shifts', headers=auth_headers, params=payload)
    response = json.loads(response.text)
    response = response['data']
    users = []
    for shift in response:
      if 'employeeId' not in shift:
        continue
      users.append(employees[shift['employeeId']])
    return users

  def get_upcoming_shifts(self):
    employees = self.get_employees()
    auth_headers = {
      'Authorization': 'Bearer ' + self.access_token,
      'X-ClientId': self.client_id
    }
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    nextMonth = (datetime.datetime.now() + relativedelta(months=1)).strftime("%Y-%m-%d")
    payload = {
      'from': today,
      'to': nextMonth
    }
    response = self.session.request("GET", self.base_url + '/scheduling/v1/shifts', headers=auth_headers, params=payload)
    response = json.loads(response.text)
    response = response['data']
    shifts = []
    #for shift in response:
    #  employee = employees[shift['employeeId']]
    #  start = shift['startDateTime']
    #  end = shift['endDateTime']
    #  shifts.append({"employee": employee, "start": start, "end": end})
    return shifts