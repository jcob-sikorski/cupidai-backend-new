import requests

import os

def send(email: str, transactional_id: str, **data_variables):
    print("SENDING EMAIL")
    response = requests.request(
        "POST", 
        "https://app.loops.so/api/v1/transactional", 
        json={
            "transactionalId": transactional_id,
            "email": email,
            "dataVariables": data_variables
        },
        headers={
            "Authorization": f"Bearer {os.getenv('LOOPS_ACCESS_TOKEN')}",
            "Content-Type": "application/json"
        }
    )
    return response
