from django.conf import settings
from json import dumps
import requests

def create_command_payload_and_send(method, data, channel):
    headers  = {'Content-type': 'application/json', 'Authorization': 'apikey ' + settings.CENTRIFUGO_API_KEY}
    command = {
        "method": method,
        "params": {
            "channel": channel,
            "data": data
        }
    }

    payload = dumps(command)
    resp = requests.post("http://centrifugo:8000/api", data=payload, headers=headers) 
    return resp.json()

