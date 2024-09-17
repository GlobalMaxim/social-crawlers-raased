import logging
import os
from random import randint
import re
from time import sleep
import uuid
from fastapi.encoders import jsonable_encoder
from datetime import datetime, timedelta
from http.client import HTTPException
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import (InvalidArgumentException,
                                        JavascriptException,
                                        WebDriverException,
                                        NoSuchCookieException,
                                        NoSuchElementException,
                                        StaleElementReferenceException)
from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.firefox.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys
from app.crawlers.data_handlers.grid_manager import get_active_grid
from app.schemas.profile_address import ProfileAddressCreate
from app.schemas.profile_link import ProfileLink, ProfileLinkCreate
from app.schemas.profile_task import ProfileTask
from app.core.config import settings
import app.crawlers.data_handlers.utils as api_utils
from app.crawlers.smm_engines.smm_engines import SmmEngine
from dateutil import parser



class ProfileTwitterScraper:
    logging.basicConfig(level=logging.WARN,
                        filename="app/logging/TwitterProfileScrapperLog.txt")
    logger = logging.getLogger(__name__)

    def __init__(self, profile_link: str, initial_data: ProfileTask, new_data: ProfileTask):
        self.initial_data = initial_data
        self.profile_link = profile_link
        self.new_data = new_data
        self.is_empty_page = False
        self.session_id = None
        self.main()
        
    
    def get_data(self):
        return self.initial_data, self.new_data

    def create_webdriver_instance(self):
        try:
            print('Start creating driver')
            options = Options()
            os.environ['DISPLAY'] = ':10.0'
            options.add_argument("--remote-debugging-port=9230")
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-notifications')
            options.add_argument('--disable-popup-blocking')
            options.add_argument('log-level=3')
            options.add_argument('--no-sandbox')
            # if self.useProxy == True:
            #     proxy = config('FULL_PROXY')
            #     options.add_argument(f'--proxy-server={proxy}')
            # options.add_argument("window-size=1920,1080")
            # options.add_argument("--headless")
            active_grid = get_active_grid('chrome')
            desired_capabilities = DesiredCapabilities.CHROME
            # driver = webdriver.Chrome(service=Service(ChromeDriverManager(os_type="mac_arm64").install()), options=options)
            driver = webdriver.Remote(
                command_executor=active_grid,
                desired_capabilities=desired_capabilities,
                options=options
            )
            self.session_id = driver.session_id
            print('Webdriver created')
            return driver
        except WebDriverException as ex:
            print('Webdriver error')
            print(str(ex))

    def acceptCookies(self, driver):
        try:
            driver.find_element(
                By.XPATH, '(//div[@tabindex="0" and @role="button"])[1]').click()
        except:
            pass

    def check_for_failure_page(self, driver):
        try:
            driver.find_element(By.XPATH, '//div[@id="ScriptLoadFailure"]//span').text
            driver.refresh()
        except:
            pass

    def extract_data_from_profile(self, driver: webdriver.Remote):
        now = datetime.now()
        try:
            occupation = driver.find_element(By.XPATH, '//span[@data-testid="UserProfessionalCategory"]/span/span').text
        except:
            occupation = None

        try:
            date_of_birth = driver.find_element(By.XPATH, '//span[@data-testid="UserBirthdate"]').text.lower().replace('born', '').strip()
            date_of_birth = self.convert_date(date_of_birth).strftime('%Y-%m-%d 00:00:00')
        except:
            date_of_birth = None
        
        try:
            location = driver.find_element(By.XPATH, '//span[@data-testid="UserLocation"]/span').text
        except:
            location = None

        links = []
        try:
            driver_links = driver.find_elements(By.XPATH, '//div[@data-testid="UserDescription"]//a')
            links = [link.get_attribute('href') for link in driver_links if 'hashtag_click' not in link]
        except:
            pass

        try:
            user_url = driver.find_element(By.XPATH, '//a[@data-testid="UserUrl"]').get_attribute('href')
            links.append(user_url)
        except:
            pass

        if occupation and not self.initial_data.occupation:
            self.initial_data.occupation = occupation
            self.new_data.occupation = occupation
        if date_of_birth and not self.initial_data.date_of_birth:
            self.initial_data.date_of_birth = date_of_birth
            self.new_data.date_of_birth = date_of_birth
        current_addresses = [i.address for i in self.initial_data.addresses]
        if location and location not in current_addresses:
            self.initial_data.addresses.append(ProfileAddressCreate(address=location, created_at=now))
            self.new_data.addresses.append(ProfileAddressCreate(address=location, created_at=now))

        if len(links) > 0:
            self.initial_data, self.new_data = api_utils.filter_profile_links(self.initial_data, self.new_data, links)

        return self.initial_data, self.new_data
                    
    def convert_date(self, date):
        datetime = parser.parse(date, fuzzy=True)
        print(datetime)
        return datetime

    def save_error_log(self, driver, exception):
        unique_id = self.get_guid()[:6]
        datetime_now = str(datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
        full_name = datetime_now + '_' + unique_id
        cwd = os.getcwd()
        path = os.path.join(cwd, 'app', 'logging', 'full_log', full_name)
        os.makedirs(path, exist_ok=True)
        driver.save_screenshot(os.path.join(path, 'screenshot.png'))
        inner_HTML = driver.find_element(By.XPATH, '//body').get_attribute('innerHTML')
        with open(os.path.join(path, 'page_dump.html'), 'w') as f:
            f.write(inner_HTML)
        with open(os.path.join(path, 'error.log'), 'w') as f:
            f.write('\n'.join([datetime_now, str(exception)]))
        common_log_path = os.path.join(cwd, 'app', 'logging', 'common_log')
        os.makedirs(common_log_path, exist_ok=True)
        with open(os.path.join(common_log_path, 'error.log'), 'a') as f:
            f.writelines('\t'.join([f'Social Request Id: {str(self.initial_data.social_request_id)}', f'Social Link Id: {str(self.initial_data.social_link)}',
                         f'Smm Engine Id: {str(self.initial_data.smm_engine_id)}', f'Smm Engine Name: {str(self.initial_data.smm_engine_name)}', f'Folder Name: {full_name}', '\n']))

    def main(self):
        print(f"Start {__name__}.main()")

        try:
            driver = self.create_webdriver_instance()
        except WebDriverException as ex:
            print(str(ex))
        try:
            sleep(2)
            driver.get(self.profile_link)
            print(f"Current page: {driver.current_url} SessionId: {self.session_id}")
            driver.maximize_window()
            driver.refresh()
            sleep(1)
            self.check_for_failure_page(driver)
            sleep(2)
            self.acceptCookies(driver)
            self.extract_data_from_profile(driver)
        except ConnectionAbortedError:
            print('Connection Error')
            # raise Exception
        except Exception as ex:
            print(str(ex))
            # raise Exception
        finally:
            driver.quit()
            
