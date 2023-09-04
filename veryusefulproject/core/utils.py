import requests
import shutil
import sys

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


def captcha_uploader(link):
    # API URL with a call to function to solve captcha
    captcha_solver_api_url = 'http://host.docker.internal:7777/solve'
    # opening the captcha image file as binary and putting it as value for key 'captcha'

    r = requests.get(link, stream=True)
    if r.status_code == 200:
        with open('screenshot.png', 'wb') as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)        

    file = {'captcha': open('screenshot.png','rb')}

    # Calling the API function as a 'POST' request with 'files' parameter
    resp = requests.post(captcha_solver_api_url, files=file)
    print("Captcha file uploaded.")

    # Fetching the captcha text from API response.
    try:
        captcha_text = resp.json()['output']
        print(captcha_text)
    except:
        print("Response not in JSON format. Please check your API code.")
        captcha_text = "NA"

    return captcha_text
