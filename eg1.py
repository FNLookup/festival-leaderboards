import requests

def getEG1Token(authParams, basicAuth):
    return requests.post('https://account-public-service-prod.ol.epicgames.com/account/api/oauth/token', data=authParams, headers={'Content-Type': 'application/x-www-form-urlencoded', 'Authorization': f"Basic {basicAuth}"}).json()['access_token']