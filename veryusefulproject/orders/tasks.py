import requests

from config import celery_app

from .utils import check_if_valid_url

from veryusefulproject.core.utils import create_command_payload_and_send


@celery_app.task()
def get_product_info(url, username):
    retailer = check_if_valid_url(url)
   
    if not retailer:
        print("This URL is not allowed.")
        return 

    print(retailer)

    channel_name = "{}#{}".format(username, username)

    resp = requests.post("http://parser:3000/", json={"url": url})
    json = resp.json()
    create_command_payload_and_send("publish", {"item": json}, channel_name)
