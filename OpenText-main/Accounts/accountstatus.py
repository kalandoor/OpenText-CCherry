import requests
import json
import configparser
import openpyxl

config = configparser.ConfigParser()
config.read('config.ini')
base_url = config.get('prismacloud', 'api_url')
username = config.get('prismacloud', 'username')
password = config.get('prismacloud', 'password')

# Function to get authentication token
def get_auth_token():
    url = f"{base_url}/login"
    payload = {
      "username": username,
      "password": password
    }
    headers = {
      'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=json.dumps(payload))
    return response.json().get("token", "")

# Save the token in the 'token' variable
token = get_auth_token()

def get_cloud_accounts():
    wb = openpyxl.Workbook()
    wb.remove(wb.active)  # Remove default sheet
    onboardedaccounts = wb.create_sheet("onboardedaccounts")
    # Add headers to the sheet
    onboardedaccounts['A1'] = 'Name'
    onboardedaccounts['B1'] = 'CSP'
    onboardedaccounts['C1'] = 'Account ID'
    onboardedaccounts['D1'] = 'Enabled'

    url = f"{base_url}/cloud"
    payload = {}
    headers = {
        'Accept': 'application/json; charset=UTF-8',
        'x-redlock-auth': token
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    accounts = [(item.get("accountId", ""), item.get("cloudType", "")) for item in response.json()]
    for accountsId, cloudType in accounts:
        url2 = f"{base_url}/cloud/{cloudType}/{accountsId}/project?excludeAccountGroupDetails=true"
        payload2 = {}
        headers2 = {
            'Accept': 'application/json; charset=UTF-8',
            'x-redlock-auth': token
        }
        data = requests.request("GET", url2, headers=headers2, data=payload2)
        status = [(item2.get("name", ""), item2.get("cloudType", ""), item2.get("accountId", ""), item2.get("enabled", "")) for item2 in data.json()]
        for name, cloud, accountID, enabled in status:
            onboardedaccounts.append([
                name,
                cloud,
                accountID,
                enabled
        ])
    wb.save("AccountStatus.xlsx")
               
get_cloud_accounts()