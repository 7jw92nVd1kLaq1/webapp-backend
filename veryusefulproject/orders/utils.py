import re

AMAZON_LINK_REGEX = "(?:https?://)?(?:[a-zA-Z0-9\-]+\.)?(?:amazon|amzn){1}\.(?P<tld>[a-zA-Z\.]{2,})\/(gp/(?:product|offer-listing|customer-media/product-gallery)/|exec/obidos/tg/detail/-/|o/ASIN/|dp/|(?:[A-Za-z0-9\-]+)/dp/)?(?P<ASIN>[0-9A-Za-z]{10})"
EBAY_LINK_REGEX = "(ebay\.com\/itm\/\d+)"

def check_if_valid_url(url):
    if check_if_amazon_url(url):
        return "Amazon"

    if check_if_ebay_url(url):
        return "eBay"

    return None


def check_if_amazon_url(url):
    result = re.search(AMAZON_LINK_REGEX, url)
    if not result:
        return ""

    return result.group()

def check_if_ebay_url(url):
    result = re.search(EBAY_LINK_REGEX, url)
    if not result:
        return ""

    return result.group()


def create_command_payload_and_send(method, data):
     headers = {'Content-type': 'application/json', 'Authorization': 'apikey ' + method}
