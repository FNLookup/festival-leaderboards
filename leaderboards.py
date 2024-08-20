import os
import requests

def main():
    eg1Params = {
        "grant_type": "device_auth",
        "account_id": os.getenv('ACCOUNT_ID'),
        "device_id": os.getenv('DEVICE_ID'),
        "secret": os.getenv('SECRET'),
        "token_type": "eg1"
    }
    token_eg1 = getEG1Token(eg1Params, os.getenv('BASIC_AUTH'))
    print(token_eg1)

def getEG1Token(authParams, basicAuth):
    request = requests.post('https://account-public-service-prod.ol.epicgames.com/account/api/oauth/token', data=authParams, headers={'Content-Type': 'application/x-www-form-urlencoded', 'Authorization': f"Basic {basicAuth}"})
    json = request.json()
    token = json['access_token']
    print('Got token!')
    return token