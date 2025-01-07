import json
import os
import random
import traceback

import requests
from bs4 import BeautifulSoup
from latest_user_agents import get_random_user_agent


def get_random_user_agent_header():
    """
    Generate a random user-agent for HTTP headers.

    :return: str: A random user-agent string.
    """
    return get_random_user_agent()


def test_proxy_list(proxy_list, target_url='https://google.com'):
    """
    Test a list of proxies and classify them as good or bad.

    :param proxy_list: List of proxies to test.
    :param target_url: URL to test the proxies against.
    :return: None
    """
    good_proxies = []
    bad_proxies = []

    for proxy in proxy_list:
        try:
            proxy_dict = {
                "http": proxy,
                "https": proxy,
                "ftp": proxy
            }
            response = requests.get(target_url, proxies=proxy_dict)
            if response.status_code == 200:
                good_proxies.append(proxy)
            else:
                bad_proxies.append(proxy)
        except Exception:
            print(traceback.format_exc())
            bad_proxies.append(proxy)

    print('\n--------------\nBAD PROXIES: \n')
    print(bad_proxies)
    print('\n--------------\nGOOD PROXIES: \n')
    print(good_proxies)


def auto_verify_proxy(proxy, verify_url=None, verify_url_header=None):
    """
    Verify if a proxy is working by attempting to connect to a URL.

    :param proxy: Proxy to verify.
    :param verify_url: Specific URL to verify the proxy against.
    :param verify_url_header: Headers to use for the verification request.
    :return: bool: True if the proxy is valid, False otherwise.
    """
    urls_to_test = ['https://google.com', 'https://www.bing.com/', 'https://pt.wikipedia.org/',
                    'https://www.reddit.com/']

    selected_url = verify_url if verify_url else random.choice(urls_to_test)
    headers = verify_url_header if verify_url_header else {}

    try:
        proxy_dict = {
            "http": proxy,
            "https": proxy,
            "ftp": proxy
        }
        response = requests.get(selected_url, proxies=proxy_dict, headers=headers, timeout=5)
        return response.status_code == 200
    except Exception:
        return False


def load_custom_proxy_list(from_database=False):
    """
    Load a custom proxy list, either from a database or another source.

    :param from_database: Boolean flag to load proxies from a database.
    :return: list: A list of proxies.
    """
    if from_database:
        return []  # Placeholder for database loading logic
    return []  # Placeholder for other source loading logic


def format_proxy(proxy_user, proxy_pass, base_proxy):
    """
    Format the proxy string using user credentials.

    :param proxy_user: Username for the proxy.
    :param proxy_pass: Password for the proxy.
    :param base_proxy: Base proxy address.
    :return: str: Formatted proxy string.
    """
    return f'http://{proxy_user}:{proxy_pass}@{base_proxy}'


def get_custom_service_proxy(proxy_user, proxy_pass, verify_url=None, verify_url_header=None, load_from_mongo=False):
    """
    Get a random proxy from the custom service, with optional verification.

    :param proxy_user: Username for the proxy.
    :param proxy_pass: Password for the proxy.
    :param verify_url: URL to verify the proxy against.
    :param verify_url_header: Headers to use for the verification request.
    :param load_from_mongo: Flag to load proxies from a MongoDB database.
    :return: str: A valid proxy.
    """
    if not proxy_user:
        try:
            return get_free_proxy_source_1(verify_url=verify_url, verify_url_header=verify_url_header)
        except Exception:
            return get_free_proxy_source_2(verify_url=verify_url, verify_url_header=verify_url_header)

    max_tries = 3
    for attempt in range(max_tries):
        selected_proxy = random.choice(load_custom_proxy_list(load_from_mongo))
        formatted_proxy = format_proxy(proxy_user, proxy_pass, selected_proxy)
        if auto_verify_proxy(formatted_proxy, verify_url=verify_url, verify_url_header=verify_url_header):
            return formatted_proxy

    try:
        return get_free_proxy_source_1(verify_url=verify_url, verify_url_header=verify_url_header)
    except Exception:
        return get_free_proxy_source_2(verify_url=verify_url, verify_url_header=verify_url_header)


def get_custom_service_proxy_simple(proxy_user, proxy_pass, load_from_mongo=False):
    """
    Get a random proxy from the custom service without verification.

    :param proxy_user: Username for the proxy.
    :param proxy_pass: Password for the proxy.
    :param load_from_mongo: Flag to load proxies from a MongoDB database.
    :return: str: A proxy.
    """
    if not proxy_user:
        raise ValueError("Please set up the user and the pass!")
    selected_proxy = random.choice(load_custom_proxy_list(load_from_mongo))
    return format_proxy(proxy_user, proxy_pass, selected_proxy)


def get_custom_service_proxy_dict(proxy_user, proxy_pass, verify=True, verify_url=None, verify_url_header=None,
                                  load_from_mongo=False):
    """
    Get a random proxy from the custom service and return it as a dictionary.

    :param proxy_user: Username for the proxy.
    :param proxy_pass: Password for the proxy.
    :param verify: Flag to verify the proxy.
    :param verify_url: URL to verify the proxy against.
    :param verify_url_header: Headers to use for the verification request.
    :param load_from_mongo: Flag to load proxies from a MongoDB database.
    :return: dict: Proxy dictionary.
    """
    if verify:
        selected_proxy = get_custom_service_proxy(proxy_user, proxy_pass, verify_url, verify_url_header,
                                                  load_from_mongo)
    else:
        selected_proxy = get_custom_service_proxy_simple(proxy_user, proxy_pass, load_from_mongo)

    return {
        "http": selected_proxy,
        "https": selected_proxy,
        "ftp": selected_proxy
    }


def get_request_headers():
    """
    Generate HTTP headers for requests.

    :return: dict: A dictionary of HTTP headers.
    """
    return {"user-agent": get_random_user_agent_header()}


def get_free_proxy_source_1(test_url="http://testing-ground.webscraping.pro/", verify_url=None, verify_url_header=None):
    """
    Obtain a free proxy from a source.

    :param test_url: URL to test the proxy.
    :param verify_url: URL to verify the proxy against.
    :param verify_url_header: Headers to use for the verification request.
    :return: str: A free proxy.
    """
    page = requests.get('https://free-proxy-list.net/', headers={'User-Agent': get_random_user_agent()})
    soup = BeautifulSoup(page.text, "lxml")
    proxies = soup.select("tbody tr")
    cache_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'free_proxies_cache.json')

    max_retries = 15
    retries = 0
    while retries < max_retries:
        proxy = ':'.join([item.text for item in random.choice(proxies).select("td")[:2]])
        if '.' not in proxy:
            continue

        try:
            with open(cache_file_path) as f:
                cached_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            cached_data = {"bad_proxies": []}

        if proxy in cached_data['bad_proxies']:
            continue

        proxy_dict = {
            "http": proxy,
            "https": proxy,
            "ftp": proxy
        }
        headers = verify_url_header if verify_url_header else {
            'User-Agent': get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        }
        if verify_url:
            test_url = verify_url

        try:
            response = requests.get(test_url, proxies=proxy_dict, timeout=4, headers=headers)
            if response.status_code == 200:
                print(f"Successful Free Proxy: {proxy}")
                return proxy
            else:
                retries += 1
        except Exception:
            print(f"Proxy error: {proxy}")
            retries += 1
            cached_data['bad_proxies'].append(proxy)
            with open(cache_file_path, 'w') as f:
                json.dump(cached_data, f)

    import urllib
    return urllib.request.getproxies()


def get_free_proxy_source_2(test_url="http://testing-ground.webscraping.pro/", verify_url=None, verify_url_header=None):
    """
    Obtain a free proxy from another source.

    :param test_url: URL to test the proxy.
    :param verify_url: URL to verify the proxy against.
    :param verify_url_header: Headers to use for the verification request.
    :return: str: A free proxy.
    """
    cache_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'free_proxies_cache.json')

    page1 = requests.get(
        'https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&sort_by=lastChecked&sort_type=desc&country=BR',
        headers={'User-Agent': get_random_user_agent()})
    page2 = requests.get(
        'https://proxylist.geonode.com/api/proxy-list?limit=500&page=2&sort_by=lastChecked&sort_type=desc&country=BR',
        headers={'User-Agent': get_random_user_agent()})
    all_proxies = page1.json()['data'] + page2.json()['data']

    max_retries = 15
    retries = 0
    for item in all_proxies:
        if retries >= max_retries:
            import urllib
            return urllib.request.getproxies()

        proxy = f"{item['ip']}:{item['port']}"
        headers = verify_url_header if verify_url_header else {
            'User-Agent': get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        }
        if verify_url:
            test_url = verify_url

        try:
            with open(cache_file_path) as f:
                cached_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            cached_data = {"bad_proxies": []}

        if proxy in cached_data['bad_proxies']:
            continue

        proxy_dict = {
            "http": proxy,
            "https": proxy,
            "ftp": proxy
        }
        try:
            response = requests.get(test_url, proxies=proxy_dict, timeout=4, headers=headers)
            if response.status_code == 200:
                print(f"Successful Free Proxy: {proxy}")
                return proxy
            else:
                retries += 1
        except Exception:
            print(f"Proxy error: {proxy}")
            retries += 1
            cached_data['bad_proxies'].append(proxy)
            with open(cache_file_path, 'w') as f:
                json.dump(cached_data, f)

    import urllib
    return urllib.request.getproxies()


def get_free_proxy_dict(verify_url=None, verify_url_header=None):
    """
    Obtain a free proxy and return it as a dictionary.

    :param verify_url: URL to verify the proxy against.
    :param verify_url_header: Headers to use for the verification request.
    :return: dict: A dictionary containing the proxy.
    """
    try:
        free_proxy = get_free_proxy_source_2(verify_url=verify_url, verify_url_header=verify_url_header)
    except Exception:
        free_proxy = get_free_proxy_source_1(verify_url=verify_url, verify_url_header=verify_url_header)

    return {
        "http": free_proxy,
        "https": free_proxy,
        "ftp": free_proxy
    }
