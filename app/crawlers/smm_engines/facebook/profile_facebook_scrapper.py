from http.client import HTTPException
from datetime import timedelta,  datetime
import io
import json
import pickle
from random import randint
from time import sleep, time
import os
import re
import uuid
import zipfile

from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webelement import WebElement
from tenacity import retry, retry_if_exception_type, wait_chain, wait_fixed
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common import exceptions
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (InvalidArgumentException,
                                        JavascriptException,
                                        WebDriverException,
                                        NoSuchCookieException,
                                        TimeoutException,
                                        NoSuchElementException,
                                        StaleElementReferenceException,
                                        SessionNotCreatedException)
import parsedatetime
import requests
from dateutil import parser

from decouple import config
import pytesseract
from PIL import Image
from app.crawlers.data_handlers.DataHandler import DataHandler, SocialTask
from app.crawlers.proxy.proxy import get_background_js, get_manifest_json
from app.schemas.profile_address import ProfileAddressCreate
from app.schemas.profile_email import ProfileEmailCreate
from app.schemas.profile_phone import ProfilePhoneCreate
from app.schemas.profile_task import ProfileTask
from app.crud.crud_social_parsing_post import social_parsing_post as crud_social_parsing_post
from app.crawlers.data_handlers.utils import  send_post_to_reply_link
from app.models.social_request import SocialRequest
import app.crawlers.data_handlers.utils as api_utils
from app.crawlers.smm_engines.smm_engines import SmmEngine
from app.core.config import settings
from app.services.account_logging.cookie_manager import change_lock_cookie_status, get_full_account_info, get_cookie_file, save_cookies_to_file, update_cookie_by_id
from app.services.twofactor.totp import get_otp
from app.logging.notify import notify


class ProfileFacebookScraper:
    def __init__(self, profile_link: str, initial_data: ProfileTask, new_data: ProfileTask):
        self.initial_data = initial_data
        self.profile_link = profile_link
        self.new_data = new_data
        self.session_id = None
        self.is_fanpage = False
        self.current_link = ""
        self.is_group = False
        if self.profile_link and '/groups/' in self.profile_link:
            self.is_group = True
            
        self.media_basedir = self.initial_data.reply_link.host
        self.is_cookie_valid = True
        self.social_account, self.active_cookie, self.proxy = get_full_account_info(2)
        self.main()

    def get_data(self):
        return self.initial_data, self.new_data

    def create_webdriver_instance(self):
        options = webdriver.ChromeOptions()
        options.add_argument("start-maximized")
        options.add_argument("--disable-blink-features")
        options.add_argument('--disable-notifications')
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.set_capability("platformName", "Linux")
        options.set_capability("browserName", "chrome")
        preferences = {
            "webrtc.ip_handling_policy" : "disable_non_proxied_udp",
            "webrtc.multiple_routes_enabled": False,
            "webrtc.nonproxied_udp_enabled" : False
        }
        options.add_experimental_option("prefs", preferences)
        if self.proxy.username is not None:
            proxy: str = "".join([str(self.proxy.ip), ":",str(self.proxy.port),"@",self.proxy.username,":",self.proxy.password])
        else:
            proxy: str = "".join([str(self.proxy.ip), ":",str(self.proxy.port)])
        proxy_parts = proxy.split("@")
        for i in proxy_parts:
            if "." in i:
                ip, port = i.split(':')
            else:
                username, password = i.split(':')
        if "@" in proxy:
            pluginfile = 'app/crawlers/proxy/proxy_auth_plugin.zip'
            with zipfile.ZipFile(pluginfile, 'w') as zp:
                zp.writestr("manifest.json", get_manifest_json())
                zp.writestr("background.js", get_background_js(ip, port, username, password))
            options.add_extension(pluginfile)
        else:
            full_proxy = f"{self.proxy.ip.exploded}:{self.proxy.port}"
            options.add_argument(f'--proxy-server=http://{full_proxy}')
        driver = webdriver.Remote(
            command_executor=settings.REMOTE_SELENIUM_GRIDS[0],
            options=options
        )
        notify.info('Driver was created')
        return driver

    def two_factor_auth(self, driver: webdriver.Remote):
        twofactor_token: str = self.social_account.twofactor_token
        twofactor_digits = get_otp(twofactor_token.upper())
        driver.find_element(By.XPATH, '//input[@id="approvals_code"]').send_keys(twofactor_digits)
        driver.find_element(By.XPATH, '//button[@id="checkpointSubmitButton"]').click()
        sleep(5)
        for _ in range(5):
            try:
                driver.find_element(By.XPATH, '//button[@value="Continue"]').click()
            except:
                pass
            try:
                driver.find_element(By.XPATH, '//button[@value="This Was Me"]').click()
            except:
                pass
            try:
                driver.find_element(By.XPATH, '//button[@value="Not Now"]').click()
            except:
                pass
            sleep(1)

    def login(self, driver: webdriver.Remote):
        try:
            driver.get('https://www.facebook.com')
            sleep(5)
            try:
                WebDriverWait(driver, timeout=5).until(EC.visibility_of_element_located(
                    (By.XPATH, '//button[@data-cookiebanner="accept_button"]')))
                driver.find_element(
                    By.XPATH, '//button[@data-cookiebanner="accept_button"]').click()
            except:
                pass
            WebDriverWait(driver, timeout=5).until(
                EC.visibility_of_element_located((By.XPATH, '//input[@name="email"]')))

            driver.find_element(
                By.XPATH, '//input[@name="email"]').send_keys(self.social_account.email)
            driver.find_element(
                By.XPATH, '//input[@name="pass"]').send_keys(self.social_account.password)
            sleep(3)
            button = driver.find_element(By.XPATH, "//button[@name='login']")
            ActionChains(driver).move_to_element(button).click().perform()
            try:
                driver.find_element(By.XPATH, '//span[contains(text(),"Your account has been disabled")]')
                self.active_cookie.is_valid = False
                update_cookie_by_id(self.active_cookie.id, self.active_cookie)
                raise TimeoutException
            except TimeoutException:
                notify.error("Your account has been disabled")
                raise TimeoutException
            except Exception:
                pass
            try:
                try:
                    is_twofactor = driver.find_element(By.XPATH, "//strong[contains(text(), 'Two-factor authentication required')]")
                except:
                    is_twofactor = None
                    pass
                try:
                    login_code = driver.find_element(By.XPATH, "//div[contains(text(), 'your login code')]")
                except:
                    login_code = None
                    pass
                if is_twofactor or login_code:
                    self.two_factor_auth(driver)
            except Exception as ex:
                notify.warning(ex)
            try:
                WebDriverWait(driver, timeout=30).until(
                    EC.visibility_of_all_elements_located((By.XPATH, '//a[contains(@href, "profile.php")]')))
                notify.info('Authenticated')
                save_cookies_to_file(driver, self.active_cookie, 'facebook', self.media_basedir, is_cookie_valid=False)
            except TimeoutException:
                notify.error(f'Cannot login with cookie_id: {self.active_cookie.id} and user email: {self.social_account.email}')
                raise TimeoutException
        except TimeoutException:
            raise TimeoutException
            # sleep(100)
        except Exception as ex:
            print(str(ex))

    def convert_date(self, date):
        datetime = parser.parse(date, fuzzy=True)
        print(datetime)
        return datetime

    def get_profile_data(self, driver: webdriver.Remote):
        now = datetime.now()
        links = []
        if not self.is_fanpage:
            driver.get(f"{self.profile_link}/about_contact_and_basic_info")

            try:
                occupation = driver.find_element(By.XPATH, '//span[text()="Category"]/ancestor::div[@class][1]/following-sibling::div//span').text
            except:
                occupation = None

            try:
                address = driver.find_element(By.XPATH, '//span[text()="Address"]/ancestor::div[@class][1]/preceding-sibling::div//span').text
            except:
                address = None

            try:
                email = driver.find_element(By.XPATH, '//span[text()="Contact info"]/ancestor::div[@class][1]/following-sibling::div//div[text()="Email"]/ancestor::li/div/div/div[1]//span').text
            except:
                email = None

            try:
                phone = driver.find_element(By.XPATH, '//span[text()="Contact info"]/ancestor::div[@class][1]/following-sibling::div//div[text()="Mobile"]/ancestor::li/div/div/div[1]//span').text
            except:
                phone = None

            try:
                date_of_birth = driver.find_element(By.XPATH, '//div[text()="Birth date"]/ancestor::span[2]/ancestor::div[1]/preceding-sibling::div//span').text
                year_of_birth = driver.find_element(By.XPATH, '//div[text()="Birth year"]/ancestor::span[2]/ancestor::div[1]/preceding-sibling::div//span').text
                date_of_birth = date_of_birth + " " + year_of_birth
                date_of_birth = self.convert_date(date_of_birth)
            except:
                date_of_birth = None

            try:
                driver_links = driver.find_elements(By.XPATH, "//div[./span[contains(text(), 'Websites and social links')]]/ancestor::div[not(@class)][1]//a")
                
                for link in driver_links:
                    ActionChains(driver).move_to_element(link).perform()
                    pattern = r'(.+)(:?\?.+)'
                    link = re.search(pattern, link.get_attribute('href')).group(1)
                    links.append(link)
            except:
                pass

            if occupation and not self.initial_data.occupation:
                self.initial_data.occupation = occupation
                self.new_data.occupation = occupation

            if date_of_birth and not self.initial_data.date_of_birth:
                self.initial_data.date_of_birth = date_of_birth
                self.new_data.date_of_birth = date_of_birth

            current_addresses = [i.address for i in self.initial_data.addresses]
            if address and address not in current_addresses:
                self.initial_data.addresses.append(ProfileAddressCreate(address=address, created_at=now))
                self.new_data.addresses.append(ProfileAddressCreate(address=address, created_at=now))

            current_emails = [i.email for i in self.initial_data.emails]
            if email and email not in current_emails:
                self.initial_data.emails.append(ProfileEmailCreate(email=email, created_at=now))
                self.new_data.emails.append(ProfileEmailCreate(email=email, created_at=now))
            
            current_mobile_phones = [i.number for i in self.initial_data.phones]
            if phone and phone not in current_mobile_phones:
                self.initial_data.phones.append(ProfilePhoneCreate(phone=phone, created_at=now))
                self.new_data.phones.append(ProfilePhoneCreate(phone=phone, created_at=now))

        elif self.is_fanpage:
            driver.get(f'{self.profile_link}/about/?ref=page_internal')
            try:
                driver_links = driver.find_elements(By.XPATH, '//span[text()="ADDITIONAL CONTACT INFO"]/ancestor::div[not(@class)][1]//a')
                links = [link.get_attribute('href') for link in driver_links]
            except:
                pass

            try:
                more_driver_links = driver.find_elements(By.XPATH, '//span[text()="MORE INFO"]/ancestor::div[not(@class)][1]/ancestor::div[1]/following-sibling::div//a')
                more_links = [link.get_attribute('href') for link in more_driver_links]
                for link in more_links:
                    if link not in links:
                        links.append(link)
            except:
                pass

            current_emails = [i.email for i in self.initial_data.emails]
            try:
                if len(links)>0:
                    for key, i in enumerate(links.copy()):
                        if 'mailto:' in i:
                            email = links.pop(key)
                            email = i.replace('mailto:', '')
                            if email not in current_emails:
                                self.initial_data.emails.append(ProfileEmailCreate(email=email, created_at=now))
                                self.new_data.emails.append(ProfileEmailCreate(email=email, created_at=now))
            except:
                pass


        # if len(links) > 0:
        self.initial_data, self.new_data = api_utils.filter_profile_links(self.initial_data, self.new_data, links)


    def main(self):
        try:
            driver = self.create_webdriver_instance()
        except Exception as ex:
            raise 
        driver.maximize_window()
        driver.get("https://www.facebook.com")
        notify.info('Facebook profile crawling was started')
        try:
            cookies = get_cookie_file(self.active_cookie, self.media_basedir)
            for cookie in cookies:
                driver.add_cookie(cookie)
            driver.refresh()
            try:

                WebDriverWait(driver, timeout=30).until(
                    EC.visibility_of_all_elements_located((By.XPATH, '//a[contains(@href, "profile.php")]')))
            except:
                raise InvalidArgumentException
            notify.info("Cookies added")
        except (InvalidArgumentException, FileNotFoundError):
            self.is_cookie_valid = False
            self.login(driver)
        try:
            driver.get(self.profile_link)
            sleep(5)
            print("Opened: ", self.profile_link)
            try:
                driver.find_element(
                    By.XPATH, '//div[@aria-label="You’re Temporarily Blocked"]//div[@aria-label="OK"]').click()
            except:
                pass
            try:
                driver.find_element(
                    By.XPATH, '//div[contains(@id, "mount")]//div[@style="top: 56px; z-index: auto;"]//span[contains(text(),"Home")]').text
                self.is_fanpage = True
            except:
                pass

            return self.get_profile_data(driver)
        except:
            pass
        finally:
            driver.quit()

