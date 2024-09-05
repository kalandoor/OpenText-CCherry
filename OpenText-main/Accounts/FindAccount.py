import requests
import json
import configparser

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

def find_account(cloud, account):
    url = f"{base_url}/cloud/{cloud}/{account}"
    payload = {}
    headers = {
        'Accept': 'application/json; charset=UTF-8',
        'x-redlock-auth': token
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    groupIDs = response.json().get("groupIds", "")
    for groupID in groupIDs:
        url2 = f"{base_url}/cloud/group/{groupID}"
        payload2 = {}
        headers2 = {
            'Accept': 'application/json; charset=UTF-8',
            'x-redlock-auth': token
        }
        response2 = requests.request("GET", url2, headers=headers2, data=payload2)
        groupName = response2.json().get("name", "")
        print(groupName)

cloud = input("Select Cloud Provider - (aws, azure, gcp): ")
account = input("Put in Valid Account ID: ")
find_account(cloud, account)