import logging
import random
import time
import traceback

from anticaptchaofficial.hcaptchaproxyless import hCaptchaProxyless
from imagetyperzapi3.imagetyperzapi import ImageTyperzAPI
from python_anticaptcha import AnticaptchaClient, NoCaptchaTaskProxylessTask

logging.basicConfig(format='%(asctime)s  %(levelname)s %(message)s', level=logging.INFO)


def solve_recaptcha(anticaptcha_key: str, captcha_url: str, sitekey: str, imagetyperz_key=None):
    """
    Solve a recaptcha challenge using available captcha solving services.

    Args:
        anticaptcha_key (str): Credential key for anti-captcha service.
        captcha_url (str): URL of the page containing the captcha.
        sitekey (str): Site key of the captcha.
        imagetyperz_key (str, optional): Credential key for imagetyperz service.

    Returns:
        str or bool: Captcha response if successful, otherwise False.
    """
    response = False
    service_choice = random.choice([1, 2]) if imagetyperz_key else 1 if anticaptcha_key else 5

    if service_choice == 1:
        logging.debug('Attempting to solve captcha using anti-captcha service.')
        response = use_service_anticaptcha(anticaptcha_key, captcha_url, sitekey)
        if not response and imagetyperz_key:
            logging.info('Retrying captcha solution using imagetyperz service.')
            response = use_service_imagetyperz(imagetyperz_key, captcha_url, sitekey)
    elif service_choice == 2:
        logging.debug('Attempting to solve captcha using imagetyperz service.')
        response = use_service_imagetyperz(imagetyperz_key, captcha_url, sitekey)
        if not response:
            logging.info('Retrying captcha solution using anti-captcha service.')
            response = use_service_anticaptcha(anticaptcha_key, captcha_url, sitekey)
    elif service_choice == 5:
        logging.debug('Attempting to solve captcha using imagetyperz service.')
        response = use_service_imagetyperz(imagetyperz_key, captcha_url, sitekey)
        if not response:
            logging.info('Retrying captcha solution using imagetyperz service.')
            response = use_service_imagetyperz(imagetyperz_key, captcha_url, sitekey)

    return response


def use_service_anticaptcha(anticaptcha_key, captcha_url, sitekey):
    """
    Solve a captcha challenge using the anti-captcha service.

    Args:
        anticaptcha_key (str): Credential key for anti-captcha service.
        captcha_url (str): URL of the page containing the captcha.
        sitekey (str): Site key of the captcha.

    Returns:
        str or bool: Captcha response if successful, otherwise False.
    """
    logging.info('Using anti-captcha service.')
    client = AnticaptchaClient(anticaptcha_key)

    try:
        task = NoCaptchaTaskProxylessTask(captcha_url, sitekey)
        job = client.createTask(task)
        job.join()
        captcha_response = job.get_solution_response()
        logging.info('The anti-captcha service successfully solved the captcha challenge.')
        return captcha_response
    except Exception as e:
        logging.warning(f'Anti-captcha service failed: {str(e)}')
        return False


def use_service_imagetyperz(imagetyperz_key, captcha_url, sitekey):
    """
    Solve a captcha challenge using the imagetyperz service.

    Args:
        imagetyperz_key (str): Credential key for imagetyperz service.
        captcha_url (str): URL of the page containing the captcha.
        sitekey (str): Site key of the captcha.

    Returns:
        str or bool: Captcha response if successful, otherwise False.
    """
    logging.info('Using imagetyperz service.')

    try:
        ita = ImageTyperzAPI(imagetyperz_key)
        recaptcha_params = {
            'page_url': captcha_url,
            'sitekey': sitekey,
            'proxy': '126.45.34.53:345',
        }
        captcha_id = ita.submit_recaptcha(recaptcha_params)
        while ita.in_progress():
            time.sleep(1)
        recaptcha_response = ita.retrieve_recaptcha(captcha_id)
        logging.info('The imagetyperz service successfully solved the captcha challenge.')
        return recaptcha_response
    except Exception as e:
        logging.warning(f'Imagetyperz service failed: {str(e)}')
        return False


def use_service_anticaptcha_hcap(anticaptcha_key: str, captcha_url: str, sitekey: str):
    """
    Solve an hcaptcha challenge using the anti-captcha service.

    Args:
        anticaptcha_key (str): Credential key for anti-captcha service.
        captcha_url (str): URL of the page containing the captcha.
        sitekey (str): Site key of the captcha.

    Returns:
        str or bool: Captcha response if successful, otherwise False.
    """
    logging.info('Using anti-captcha hCaptcha service.')

    solver = hCaptchaProxyless()
    solver.set_verbose(1)
    solver.set_key(anticaptcha_key)
    solver.set_website_url(captcha_url)
    solver.set_website_key(sitekey)

    response = solver.solve_and_return_solution()
    if response != 0:
        logging.info('The anti-captcha hCaptcha service successfully solved the captcha challenge.')
        return response
    else:
        logging.warning('Anti-captcha hCaptcha service failed.')
        return False


def check_balance(imagetyperz_key, anticaptcha_key):
    """
    Check the balance of imagetyperz and anti-captcha accounts.

    Args:
        imagetyperz_key (str): Credential key for imagetyperz service.
        anticaptcha_key (str): Credential key for anti-captcha service.
    """
    ita = ImageTyperzAPI(imagetyperz_key)
    imagetyperz_balance = ita.account_balance()
    logging.info(f'Imagetyperz balance: {imagetyperz_balance}')

    client = AnticaptchaClient(anticaptcha_key)
    anticaptcha_balance = client.getBalance()
    logging.info(f'Anti-captcha balance: {anticaptcha_balance}')
