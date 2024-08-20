import os
import eg1

def main():
    eg1Params = {
        "grant_type": "device_auth",
        "account_id": os.getenv('ACCOUNT_ID'),
        "device_id": os.getenv('DEVICE_ID'),
        "secret": os.getenv('SECRET'),
        "token_type": "eg1"
    }
    token_eg1 = eg1.getEG1Token(eg1Params, os.getenv('BASIC_AUTH'))
    print(token_eg1)