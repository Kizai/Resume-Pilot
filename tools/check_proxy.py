import os
import json
import time
import requests
from tools.toolbox import get_conf
from tools.logginger import get_logger

logger = get_logger()


def check_proxy(proxies=None):
    """
    Check the location of the proxy server and print the result.

    :param proxies: (optional) A dictionary containing the proxy configuration, e.g. {'https': 'https://proxy.example.com'}
    :return: A string describing the proxy server location or an error message.
    """
    proxies_https = proxies['https'] if proxies else 'None'
    url = "https://ipapi.co/json/"

    try:
        response = requests.get(url, proxies=proxies, timeout=4)
        data = response.json()
        logger.info(data)

        if 'country_name' in data:
            country = data['country_name']
        elif 'error' in data:
            country = "location unknown, IP lookup rate limit reached"
        else:
            country = "location unknown"
    except requests.exceptions.RequestException:
        country = "location lookup timed out, proxy may be invalid"

    result = f"Proxy configuration {proxies_https}, located in: {country}"
    logger.info(result)
    return result


if __name__ == '__main__':
    os.environ['no_proxy'] = '*'
    proxies = get_conf()
    check_proxy(proxies)
