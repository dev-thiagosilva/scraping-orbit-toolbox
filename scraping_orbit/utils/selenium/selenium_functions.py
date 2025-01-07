import logging
import os
import platform
import random
import time
from pathlib import Path

import undetected_chromedriver as uc
from playwright.sync_api import sync_playwright
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager

REPOSITORY_PATH = Path(__file__).parent.parent.parent


def initialize_selenium_webdriver(webdriver_type=None, headless=False, download_path=None, profile=None,
                                  undetectable=False, allow_download_images=True, random_useragent=False,
                                  custom_useragent='', custom_chromedriver_path=None, custom_geckodriver_path=None,
                                  custom_proxy_value=None):
    """
    Initialize a Selenium WebDriver instance.
    :param webdriver_type: Choose between Chrome and Firefox.
    :param headless: Whether the browser should run in headless mode.
    :param download_path: Custom path for downloads.
    :param profile: Firefox profile path.
    :param undetectable: Whether the browser is undetectable for anti-bot systems.
    :param allow_download_images: Allow image loading.
    :param random_useragent: Use a random user agent.
    :param custom_useragent: Use a custom user agent.
    :param custom_chromedriver_path: Custom path for chromedriver executable.
    :param custom_geckodriver_path: Custom path for geckodriver executable.
    :param custom_proxy_value: Custom proxy value.
    :return: WebDriver instance.
    """
    global browser

    download_path = download_path or REPOSITORY_PATH / "working_directory/downloads"
    download_path.mkdir(parents=True, exist_ok=True)

    if undetectable:
        browser = initialize_undetected_chromedriver(headless_mode=headless)
    else:
        if webdriver_type.upper() == 'FIREFOX':
            browser = initialize_firefox_webdriver(headless, download_path, profile, custom_useragent,
                                                   custom_geckodriver_path)
        elif webdriver_type.upper() == 'CHROME':
            browser = initialize_chrome_webdriver(headless, download_path, random_useragent, custom_useragent,
                                                  custom_chromedriver_path)

    return browser


def initialize_firefox_webdriver(headless, download_path, profile, custom_useragent, custom_geckodriver_path):
    gecko_executable_path = custom_geckodriver_path or GeckoDriverManager().install()
    options = Options()
    options.headless = headless
    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.download.manager.showWhenStarting", False)
    options.set_preference("browser.helperApps.alwaysAsk.force", False)
    options.set_preference("browser.download.dir", str(download_path))
    options.set_preference("browser.helperApps.neverAsk.saveToDisk",
                           "text/plain, application/octet-stream, application/binary, text/csv, application/csv,"
                           " application/excel, text/comma-separated-values, text/xml, application/xml,"
                           " image/svg+xml, image/svg,image/SVG, image/png,image/x-citrix-png,image/x-png")

    capabilities = webdriver.DesiredCapabilities.FIREFOX
    capabilities['marionette'] = True

    if profile:
        firefox_profile = webdriver.FirefoxProfile(profile)
        firefox_profile.set_preference("general.useragent.override", custom_useragent)
        firefox_profile.set_preference("dom.webdriver.enabled", False)
        firefox_profile.set_preference('useAutomationExtension', False)
        firefox_profile.update_preferences()
        browser = webdriver.Firefox(executable_path=gecko_executable_path, options=options,
                                    capabilities=capabilities, firefox_profile=firefox_profile)
    else:
        browser = webdriver.Firefox(executable_path=gecko_executable_path, options=options,
                                    capabilities=capabilities)

    return browser


def initialize_chrome_webdriver(headless, download_path, random_useragent, custom_useragent, custom_chromedriver_path):
    chrome_executable_path = custom_chromedriver_path or ChromeDriverManager().install()
    options = webdriver.ChromeOptions()
    options.headless = headless
    options.add_argument("--window-size=1920,1080")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--disable-blink-features=AutomationControlled')

    if random_useragent:
        options.add_argument(f'user-agent={custom_useragent}')
    if custom_useragent:
        options.add_argument(f'user-agent={custom_useragent}')

    prefs = {'download.default_directory': str(download_path)}
    options.add_experimental_option('prefs', prefs)

    browser = webdriver.Chrome(executable_path=chrome_executable_path, options=options)

    return browser


def initialize_undetected_chromedriver(headless_mode=True, version=113):
    """
    Initializes undetectable chromedriver
    :param version: uc main version
    :param headless_mode: If it will run on headless
    :return: Driver
    """
    options = uc.ChromeOptions()
    if headless_mode:
        options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-setuid-sandbox")
    driver = uc.Chrome(options=options, version_main=version)

    return driver


def initialize_playwright(browser_type="firefox", headless_mode=False, proxy_value=None):
    """
    Initialize Playwright browser instance.
    :param browser_type: Type of browser (firefox, chromium, webkit).
    :param headless_mode: Whether the browser should run in headless mode.
    :param proxy_value: Proxy value.
    :return: Browser instance.
    """
    with sync_playwright() as playwright:
        if browser_type == "chromium":
            return playwright.chromium.launch(headless=headless_mode,
                                              args=[f"--proxy-server=http://{proxy_value}"] if proxy_value else None)
        elif browser_type == "firefox":
            return playwright.firefox.launch(headless=headless_mode)
        elif browser_type == "webkit":
            return playwright.webkit.launch(headless=headless_mode)
        else:
            raise ValueError(f"Unsupported browser type: {browser_type}")


def install_chrome():
    """
    Installs Google Chrome on the system.
    """
    if platform.system() == 'Windows':
        os.system('start chrome')
    elif platform.system() == 'Linux':
        os.system('wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb')
        os.system('sudo dpkg -i google-chrome-stable_current_amd64.deb')
        os.system('sudo apt-get install -f')
        os.system('rm google-chrome-stable_current_amd64.deb')
    else:
        print('Unsupported operating system.')


def wait_element_appear(driver, xpath, wait_time=10):
    """
    Wait for an element to appear.
    :param driver: WebDriver instance.
    :param xpath: XPath of the element.
    :param wait_time: Maximum wait time in seconds.
    :return: True if element appears, else False.
    """
    try:
        WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.XPATH, xpath)))
        logging.debug("Element appeared.")
        return True
    except TimeoutException:
        logging.debug("Element did not appear.")
        return False


def wait_element_disappear(driver, xpath, wait_time=10):
    """
    Wait for an element to disappear.
    :param driver: WebDriver instance.
    :param xpath: XPath of the element.
    :param wait_time: Maximum wait time in seconds.
    """
    try:
        WebDriverWait(driver, wait_time).until_not(EC.presence_of_element_located((By.XPATH, xpath)))
        logging.debug("Element disappeared.")
    except TimeoutException:
        logging.debug("Element did not disappear.")


def wait_loading(driver, xpath, wait_time=10):
    """
    Wait for an element to load and then disappear.
    :param driver: WebDriver instance.
    :param xpath: XPath of the element.
    :param wait_time: Maximum wait time in seconds.
    """
    try:
        WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.XPATH, xpath)))
        logging.debug("Element loaded.")
    except TimeoutException:
        logging.debug("Element did not load.")

    try:
        WebDriverWait(driver, wait_time).until_not(EC.presence_of_element_located((By.XPATH, xpath)))
        logging.debug("Element disappeared.")
    except TimeoutException:
        logging.debug("Element did not disappear.")


def scroll_down(driver, times=1, scroll_seconds=1, to_bottom=False):
    """
    Scroll down a webpage.
    :param driver: WebDriver instance.
    :param times: Number of scrolls.
    :param scroll_seconds: Seconds to wait between scrolls.
    :param to_bottom: Scroll to the bottom of the page.
    """
    for _ in range(times):
        if to_bottom:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        else:
            body = driver.find_element(By.CSS_SELECTOR, 'body')
            body.send_keys(Keys.PAGE_DOWN)
        time.sleep(scroll_seconds)


def scroll_down_infinite(driver, scroll_time=1, to_bottom=False):
    """
    Scroll down a webpage infinitely.
    :param driver: WebDriver instance.
    :param scroll_time: Seconds to wait between scrolls.
    :param to_bottom: Scroll to the bottom of the page.
    """
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        if to_bottom:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        else:
            body = driver.find_element(By.CSS_SELECTOR, 'body')
            body.send_keys(Keys.PAGE_DOWN)

        time.sleep(scroll_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


def select_option(element, option_text):
    """
    Select an option from a dropdown list.
    :param element: WebElement representing the dropdown.
    :param option_text: Text of the option to select.
    :return: True if option selected, else False.
    """
    try:
        for option in element.find_elements(By.TAG_NAME, 'option'):
            if option_text in option.text:
                option.click()
                return True
        return False
    except Exception as e:
        logging.error(f"Failed to select option: {e}")
        return False


def type_slowly(element, value, interval=0.5):
    """
    Type a value into an element slowly.
    :param element: WebElement to type into.
    :param value: Text to type.
    :param interval: Interval between keystrokes.
    """
    for char in value:
        element.send_keys(char)
        time.sleep(interval)


def save_page_source(driver, filename='page.html'):
    """
    Save the page source to a file.
    :param driver: WebDriver instance.
    :param filename: File name to save the HTML.
    """
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(driver.page_source)


def save_html(html, filename='page.html'):
    """
    Save HTML content to a file.
    :param html: HTML content.
    :param filename: File name to save the HTML.
    """
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(html)


def switch_to_iframe(driver, element_type, iframe_name):
    """
    Switch to a specific iframe.
    :param driver: WebDriver instance.
    :param element_type: Type of element to find iframe (e.g., id, name).
    :param iframe_name: Name of the iframe.
    """
    iframe = driver.find_element(By.XPATH, f'//iframe[@{element_type}="{iframe_name}"]')
    driver.switch_to.frame(iframe)


def switch_to_default_content(driver):
    """
    Switch to the default content.
    :param driver: WebDriver instance.
    """
    driver.switch_to.default_content()


def scheduled_interrupt_chrome_process():
    """
    Interrupt Chrome process for maintenance at scheduled times.
    """
    now = time.localtime()
    if now.tm_min in {0, 1, 2, 3, 4, 5, 25, 26, 27, 28, 29, 30}:
        print('Maintenance time...')
        time.sleep(420 if now.tm_min in {0, 25} else 360 if now.tm_min in {1, 26} else 300 if now.tm_min in {2, 27}
                   else 240 if now.tm_min in {3, 28} else 180 if now.tm_min in {4, 29} else 120)


def scheduled_kill_chrome_process_linux():
    """
    Kill Chrome processes at scheduled times on Linux.
    """
    flag = False
    while True:
        now = time.localtime()
        if now.tm_min in {56, 31}:
            if flag:
                os.system("pkill chrome")
                print('Killed Chrome processes')
                flag = False
        else:
            flag = True
        time.sleep(5)


def get_cookies_as_dict(driver):
    """
    Get cookies as a dictionary from the WebDriver.
    :param driver: WebDriver instance.
    :return: Dictionary of cookies.
    """
    cookies = driver.get_cookies()
    return {cookie['name']: cookie['value'] for cookie in cookies}


def get_random_string():
    """
    Generate a random string of numbers.
    :return: Random string.
    """
    return ''.join(str(random.randint(1, 99999)) for _ in range(8))
