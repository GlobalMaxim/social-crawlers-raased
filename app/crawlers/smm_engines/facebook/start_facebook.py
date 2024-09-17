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

import parsedatetime
import requests
from dateutil import parser
from decouple import config
import pytesseract
from PIL import Image

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

from app.crawlers.data_handlers.DataHandler import DataHandler, SocialTask
from app.crawlers.proxy.proxy import get_background_js, get_manifest_json
from app.schemas.social_account import SocialAccount
from app.schemas.social_parsing_post import SocialParsingPostCreate
from app.schemas.social_post_attachment import SocialPostAttachmentCreate
from app.schemas.social_post_stat import SocialPostStatCreate
from app.schemas.social_post_reaction import SocialPostReactionCreate
from app.schemas.social_post_request import SocialPostRequestCreate
from app.crud.crud_social_parsing_post import social_parsing_post as crud_social_parsing_post
from app.crawlers.data_handlers.utils import  send_post_to_reply_link
from app.models.social_request import SocialRequest
import app.crawlers.data_handlers.utils as api_utils
from app.crawlers.smm_engines.smm_engines import SmmEngine
from app.core.config import settings
from app.services.account_logging.cookie_manager import change_lock_cookie_status, get_full_account_info, get_cookie_file, save_cookies_to_file, update_cookie_by_id
from app.services.twofactor.totp import get_otp
from app.logging.notify import notify


class FacebookScraper:
    def __init__(self, data: SocialTask):
        self.initial_data = data
        self.is_empty_page = False
        self.session_id = None
        self.is_fanpage = False
        self.current_link = ""
        self.is_group = False
        if self.initial_data.social_link and '/groups/' in self.initial_data.social_link:
            self.is_group = True
            
        self.media_basedir = self.initial_data.reply_link.host
        self.unique_posts = set()
        self.is_cookie_valid = True
        self.social_account, self.active_cookie, self.proxy = get_full_account_info(self.initial_data.smm_engine_id)
        # self.user_account: SocialAccount = SocialAccount(**DataHandler().get_active_account(self.initial_data.smm_engine_id)[0])
        # print(self.initial_data)
        self.OS = 'Ubuntu'
        self.main()

    @retry(retry=retry_if_exception_type(SessionNotCreatedException),wait=wait_chain(*[wait_fixed(10) for i in range(6)]))
    def create_firefox_instance(self):
        options = webdriver.ChromeOptions()
        options.add_argument("start-maximized")
        options.add_argument("--disable-blink-features")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.set_capability("platformName", "Linux")
        options.set_capability("browserName", "chrome")
        preferences = {
            "webrtc.ip_handling_policy" : "disable_non_proxied_udp",
            "webrtc.multiple_routes_enabled": False,
            "webrtc.nonproxied_udp_enabled" : False
            # "enforce-webrtc-ip-permission-check": True
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
            # pass
            full_proxy = f"{self.proxy.ip.exploded}:{self.proxy.port}"

            options.add_argument(f'--proxy-server=http://{full_proxy}')

        # driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        # desired_capabilities = DesiredCapabilities.CHROME
        
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
                save_cookies_to_file(driver, self.active_cookie, self.initial_data.smm_engine_name, self.media_basedir, is_cookie_valid=False)
            except TimeoutException:
                notify.error(f'Cannot login with cookie_id: {self.active_cookie.id} and user email: {self.social_account.email}')
                raise TimeoutException
        except TimeoutException:
            raise TimeoutException
        except Exception as ex:
            print(str(ex))

    def generate_query(self, data: SocialTask):
        print('Generating query')
        keyword = data.keyword
        hashtag = data.hashtag

        if keyword != "":
            key = self.prepare_keywords(keyword)
        if keyword != "":
            return f'https://www.facebook.com/search/posts?q={key}&filters=eyJyZWNlbnRfcG9zdHM6MCI6IntcIm5hbWVcIjpcInJlY2VudF9wb3N0c1wiLFwiYXJnc1wiOlwiXCJ9In0%3D'
        elif hashtag != "":
            return f'https://www.facebook.com/hashtag/{hashtag}'

    def prepare_keywords(self, keyword):
        keyword = keyword.replace(' ', '%20').lower()
        return keyword

    def check_for_empty_page(self, driver):
        try:
            empty_text = driver.find_element(
                By.XPATH, '//*[contains(text(), "//*[contains(text(), "find any results")]")]')
        except:
            empty_text = None
            pass
        if empty_text != None:
            print('No data on page: ', self.current_link,
                  " SessionId: ", self.session_id)
            # self.save_error_log(driver,"No data on current page")
            self.is_empty_page = True
            raise ValueError

    def scroll_down_page(self, driver, last_position, num_seconds_to_load=4, scroll_attempt=0, max_attempts=5):
        end_of_scroll_region = False
        # driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        body = driver.find_element(By.CSS_SELECTOR, 'body')
        for _ in range(randint(1, 2)):
            body.send_keys(Keys.PAGE_DOWN)
        sleep(num_seconds_to_load)
        curr_position = driver.execute_script("return window.pageYOffset;")
        if curr_position == last_position:
            if scroll_attempt < max_attempts:
                end_of_scroll_region = True
            else:
                self.scroll_down_page(last_position, curr_position, scroll_attempt + 1)
        last_position = curr_position
        return last_position, end_of_scroll_region

    def collect_all_tweets_from_current_view(self, driver, lookback_limit=5):
        if self.is_group:
            page_cards = driver.find_elements(
                By.XPATH, '//div[@role="feed"]/div[.//div[@aria-describedby]]')
        elif not self.is_fanpage and self.initial_data.social_link:
            page_cards = driver.find_elements(
                By.XPATH, '//div[contains(@id, "mount")]//div[@role="main"]/div[./div][3]/div[2]/div/div[2]/div/div[./div and not(@*)]')
        elif self.is_fanpage:
            page_cards = driver.find_elements(
                By.XPATH, '//div[contains(@id, "mount")]//div[@role="main"]//div[@role="main"]/div/div[@role="feed" and not(contains(.//span,"Pinned post"))]/div[.//div[@aria-describedby]] | //div[contains(@id, "mount")]//div[@role="main"]//div[@role="main"]/div/div[.//div[@aria-describedby] and not(@role="feed")]')
        elif self.initial_data.keyword:
            page_cards = driver.find_elements(
                By.XPATH, '//div[@role="feed"]/div[not(@*)]')
        elif self.initial_data.hashtag:
            page_cards = driver.find_elements(
                By.XPATH, '//div[@role="main"]/div[./div][3]/div/div/div/div/div/div/div[./div and not(@*)]')
        # print(len(page_cards))
        if len(page_cards) <= lookback_limit:
            return page_cards
        else:
            return page_cards[-lookback_limit:]

    def get_text_from_image(self, image):
        image = Image.open(io.BytesIO(image))
        text = pytesseract.image_to_string(image, lang="eng")
        return text

    def delete_trash_files(self, post: SocialParsingPostCreate):
        trash_files = []
        trash_files.append(post.video_image)
        trash_files.append(post.featured_image)
        for attachment in post.social_posts_attachments:
            trash_files.append(attachment.image_path)
            trash_files.append(attachment.video_path)
        for file_path in trash_files:
            if file_path:
                os.remove(os.path.join(os.getcwd(), file_path))

    def convert_date(self, date):
        datetime = parser.parse(date, fuzzy=True)
        print(datetime)
        return datetime

    def get_detailed_reactions(self, driver: webdriver.Remote, path = '//div//div//span[@aria-hidden]/ancestor::div[@role="button"][1]'):
        try:
            driver.find_element(By.XPATH, path).click()
            WebDriverWait(driver, timeout=10).until(
                EC.visibility_of_element_located((By.XPATH, '(//div[@role="dialog"]//div[@role="tablist"])[1]')))
            dialog_elements = driver.find_elements(By.XPATH, '(//div[@role="dialog"]//div[@role="tablist"])[1]//div[@aria-label and .//img]')
            social_post_reactions = [] 
            for emoji in dialog_elements:
                attr = emoji.get_attribute('aria-label')
                reaction, likes = attr.split(',')
                likes = api_utils.prepare_reactions_to_int(likes.strip())
                social_post_reactions.append(SocialPostReactionCreate(reaction=reaction.upper(), count=likes))
            driver.find_element(By.XPATH, '(//div[@role="dialog"]//div[@role="tablist"])[1]//ancestor::div[not(@*)][1]//div[@aria-label="Close"]').click()
            WebDriverWait(driver, timeout=10).until(
                EC.invisibility_of_element_located((By.XPATH, '(//div[@role="dialog"]//div[@role="tablist"])[1]')))
            return social_post_reactions
        except Exception as ex:
            print(str(ex))
            return []

    def get_final_post_date(self, text_date):
        if 'ih' in text_date or 'Lh' in text_date:
            post_date = datetime.today()-timedelta(hours=1)
        elif 'Bh' in text_date:
            post_date = datetime.today()-timedelta(hours=8)
        elif 'Ah' in text_date:
            post_date = datetime.today()-timedelta(hours=4)
        elif 'Th' in text_date:
            post_date = datetime.today()-timedelta(hours=7)
        elif re.search(r"^(\d+)(?:h)$", text_date):
            delta = int(re.search(r"^(\d+)(?:h)$", text_date).group(1))
            post_date = datetime.today()-timedelta(hours=delta)
        elif re.search(r"^(\d+)(?:m)$", text_date):
            delta = int(re.search(r"^(\d+)(?:m)$", text_date).group(1))
            post_date = datetime.today()-timedelta(minutes=delta)
        elif re.search(r"^(\d+)(?:s)$", text_date):
            delta = int(re.search(r"^(\d+)(?:s)$", text_date).group(1))
            post_date = datetime.today()-timedelta(seconds=delta)
        elif text_date.lower() == "just now":
            text_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        else:
            post_date = self.convert_date(text_date)
            datetime_limit = datetime.today()-timedelta(days=7)
            datetime_limit = datetime_limit.strftime('%Y-%m-%d')
            post_date_to_datetime = post_date.strftime('%Y-%m-%d')
            if post_date_to_datetime < datetime_limit:
                raise StopIteration
        post_date = post_date.strftime('%Y-%m-%d %H:%M:%S')
        return post_date

    def extract_data_from_watch_page(self, driver: webdriver.Remote):
        WebDriverWait(driver, timeout=10).until(
            EC.visibility_of_element_located((By.XPATH, '//div[@id="watch_feed"]/div/div[@style]/div/div/div[2]/div[1]')))

        post = driver.find_element(By.XPATH, '(//div[@role="main"]//div[@style])[1]')
        try:
            left_part = driver.find_element(
                By.XPATH, '//div[@id="watch_feed"]/div/div[@style]/div/div/div[1]')
            right_part_header = driver.find_element(
                By.XPATH, '//div[@id="watch_feed"]/div/div[@style]/div/div/div[2]/div[1]')
        except:
            pass
        try:
            text_date = right_part_header.find_element(
                By.XPATH, './div[1]//a[@href="#"]/span')
            sleep(1)
            post_date_image = text_date.screenshot_as_png
            text_date = self.get_text_from_image(post_date_image).strip()
            post_date = self.get_final_post_date(text_date)
        except StopIteration:
            raise StopIteration
        except Exception as ex:
            post_date = None
            print('post_date exception')
            raise

        try:
            right_part_header.find_element(
                By.XPATH, './/div[contains(text(), "See more")]').click()
        except:
            pass

        source_link = driver.current_url

        try:
            content_arr = []
            content_elem = right_part_header.find_elements(
                By.XPATH, './div[not(@*)]//div[contains(@style,"text-align")]')
            for elem in content_elem:
                text = elem.text.strip()
                if text not in [" ", '\t', ""]:
                    content_arr.append(text + "\n")

            content = "".join(content_arr)
            if self.initial_data.social_link:
                if self.initial_data.hashtag and self.initial_data.hashtag.lower() not in content.lower():
                    return None
                elif self.initial_data.keyword and self.initial_data.keyword.lower() not in content.lower():
                    return None
        except:
            content = None

        try:
            user_name = right_part_header.find_element(
                By.XPATH, './/h2[.//a]//strong/span').text
        except:
            user_name = None
            pass

        try:
            pattern = r'(?:https:\/\/www\.facebook\.com\/)(\w+)'
            user_link = right_part_header.find_element(
                By.XPATH, './/h2[.//a]//a').get_attribute('href')
            user_login = re.search(pattern, user_link).group(1)
        except:
            user_login = None
            pass
        try:
            reactions_line = left_part.find_element(
                By.XPATH, './div[2]/div[2]/div/div/div[2]')
        except:
            pass
        try:
            likes = reactions_line.find_element(By.XPATH, './div/div/div//span').text
            pattern = r"(?: *)([0-9]+K*)(?: *)"
            like_count = re.search(pattern, likes).group(1)
            like_count = api_utils.prepare_reactions_to_int(likes)
        except:
            like_count = None

        try:
            comments = reactions_line.find_element(
                By.XPATH, "./div/div[.//span[contains(text(), 'comment')]]//span").text
            comments = str(comments.replace(' comments', '').replace(' comment', ''))
            comment_count = api_utils.prepare_reactions_to_int(comments)

        except:
            comment_count = None

        try:
            wind_sz = driver.get_window_size()
            if post.size['height'] > wind_sz['height']:
                w = driver.execute_script('return document.body.parentNode.scrollWidth')
                driver.set_window_size(w, post.size['height'] + wind_sz['height'])
                sleep(2)
            image = post.screenshot_as_png
            featured_image = api_utils.save_byte_image(image, self.media_basedir, SmmEngine.facebook)
        except:
            pass

        social_post_reactions = self.get_detailed_reactions(driver, path='(//div/span[@aria-label]/following-sibling::div[@role="button" and //span])[1]')
        post_stats = SocialPostStatCreate(likes=like_count, comments=comment_count)

        social_parsing_post = SocialParsingPostCreate(
            social_request_id=self.initial_data.social_request_id,
            smm_id=self.initial_data.smm_engine_id,
            link_id=self.initial_data.social_link_id,
            account_name=user_name,
            account_login=user_login,
            featured_image=featured_image,
            content=content,
            source_link=source_link,
            crawler_name="selenium-facebook-crawler-v1",
            date_of_news=post_date,
            social_posts_stats=post_stats
        )

        social_parsing_post.social_posts_reactions = social_post_reactions

        return social_parsing_post

    def extract_data_from_photos_page(self, driver: webdriver.Remote):
        post = driver.find_element(By.XPATH, '//div[@role="main"]')
        try:
            title_block = driver.find_element(
                By.XPATH, '//div[@role="complementary"]/div/div/div/div[1]/div[@class and .//h2//a]/div[not(@*)]/div[1]')
            content_block = driver.find_element(
                By.XPATH, '//div[@role="complementary"]/div/div/div/div[1]/div[@class and .//h2//a]/div[not(@*)]/div[2]')
        except:
            pass
        try:
            post_date_text = title_block.find_element(
                By.XPATH, './/span[./a[@href="#"]]')
            sleep(1)
            post_date_image = post_date_text.screenshot_as_png
            text_date = self.get_text_from_image(post_date_image).strip()
            post_date = self.get_final_post_date(text_date)
        except StopIteration:
            raise StopIteration
        except Exception as ex:
            post_date = None
            print('post_date exception')
            print(str(ex))

        try:
            content_block.find_element(
                By.XPATH, './/div[contains(text(), "See more")]').click()
        except:
            pass

        try:
            user_name = title_block.find_element(By.XPATH, './/h2//a').text
        except:
            user_name = None

        try:
            user_link = title_block.find_element(
                By.XPATH, './/h2//a').get_attribute('href')
            pattern = r'(?:https:\/\/www\.facebook\.com\/)(\w+)'
            user_login = re.search(pattern, user_link).group(1)
        except:
            user_login = None

        try:
            content_elem = content_block.find_element(By.XPATH, './span').text

            content = content_elem.replace('See less', '')
            if self.initial_data.social_link:
                if self.initial_data.hashtag and self.initial_data.hashtag.lower() not in content.lower():
                    return None
                elif self.initial_data.keyword and self.initial_data.keyword.lower() not in content.lower():
                    return None
        except:
            content = None

        source_link = driver.current_url

        try:
            image_link = driver.find_element(
                By.XPATH, '//div[@role="main"]//img').get_attribute('src')
            links_out = api_utils.save_image(
                [image_link], self.media_basedir, SmmEngine.facebook)
            featured_image = links_out[0]
        except:
            featured_image = None

        try:
            likes = driver.find_element(
                By.XPATH, '//div[@role="complementary"]/div/div/div/div[1]/div[not(@*)]//span[@aria-hidden]/span/span').text
            pattern = r"(?: *)([0-9]+K*)(?: *)"
            like_count = str(likes)
            like_count = re.search(pattern, like_count).group(1)
            like_count = api_utils.prepare_reactions_to_int(like_count)
        except Exception as ex:
            like_count = 0

        try:
            comments = driver.find_element(
                By.XPATH, '//div[@role="complementary"]//div/div[./div][2]//div[@role and .//i[contains(@style, "-4")]]//span').text
            comments = str(comments.replace(' comments', '').replace(' comment', ''))
            comments = api_utils.prepare_reactions_to_int(comments)
        except Exception as ex:
            comments = 0

        try:
            shares = driver.find_element(
                By.XPATH, '//div[@role="complementary"]//div/div[./div][2]//div[@role and .//i[contains(@style, "-6")]]//span').text
            shares = str(shares.replace(' shares', '').replace(' share', ''))
            shares = api_utils.prepare_reactions_to_int(shares)
        except Exception as ex:
            shares = 0

        social_post_reactions = self.get_detailed_reactions(driver)

        if featured_image == None:
            wind_sz = driver.get_window_size()
            if post.size['height'] > wind_sz['height']:
                w = driver.execute_script('return document.body.parentNode.scrollWidth')
                driver.set_window_size(w, post.size['height'] + wind_sz['height'])
                sleep(2)
            image = post.screenshot_as_png
            featured_image = api_utils.save_byte_image(image, self.media_basedir, SmmEngine.facebook)

        social_parsing_post = SocialParsingPostCreate(
            social_request_id=self.initial_data.social_request_id,
            link_id=self.initial_data.social_link_id,
            account_name=user_name,
            account_login=user_login,
            content=content,
            featured_image=featured_image,
            source_link=source_link,
            crawler_name="selenium-facebook-crawler-v1",
            date_of_news=post_date,
            smm_id=self.initial_data.smm_engine_id
        )

        social_post_stats = SocialPostStatCreate(
            likes=like_count,
            comments=comments,
            retweets=shares
        )
        social_parsing_post.social_posts_reactions = social_post_reactions
        social_parsing_post.social_posts_stats = social_post_stats
        return social_parsing_post

    def extract_data_from_videos_page(self, driver: webdriver.Remote):
        post = driver.find_element(By.XPATH, '//div[@role="main" and not(@aria-label)]')
        WebDriverWait(driver, timeout=10).until(
            EC.visibility_of_element_located((By.XPATH, '//span[not(@*)]/span[not(@*)]')))
        try:
            header_block = driver.find_element(
                By.XPATH, '//div[@role="complementary"]/div/div/div/div/div/div[1]')
        except:
            pass
        try:
            post_date_text = driver.find_element(
                By.XPATH, '//span[not(@*)]/span[not(@*)]')
            sleep(1)
            post_date_image = post_date_text.screenshot_as_png
            text_date = self.get_text_from_image(post_date_image).strip()
            post_date = self.get_final_post_date(text_date)
        except StopIteration:
            raise StopIteration
        except Exception as ex:
            post_date = None
            print('post_date exception')
            print(str(ex))

        try:
            user_link = header_block.find_element(
                By.XPATH, './/h2//a').get_attribute('href')
            pattern = r'(?:https:\/\/www\.facebook\.com\/)(\w+)'
            user_login = re.search(pattern, user_link).group(1)
        except:
            user_login = None

        try:
            user_name = header_block.find_element(By.XPATH, './/h2//a').text
        except:
            user_name = None

        try:
            header_block.find_element(
                By.XPATH, './/div[contains(text(), "See more")]').click()
        except:
            pass

        try:
            content_arr = []
            content_elem = header_block.find_elements(
                By.XPATH, './div[not(@*)]//div[contains(@style,"text-align")]')
            for elem in content_elem:
                text = elem.text.strip()
                if text not in [" ", '\t', ""]:
                    content_arr.append(text + "\n")

            content = "".join(content_arr)
            if self.initial_data.social_link:
                if self.initial_data.hashtag and self.initial_data.hashtag.lower() not in content.lower():
                    return None
                elif self.initial_data.keyword and self.initial_data.keyword.lower() not in content.lower():
                    return None
        except:
            content = None

        source_link = driver.current_url

        try:
            likes = driver.find_element(
                By.XPATH, '//div[@role="complementary"]/div/div/div/div/div/div[2]//span[@aria-hidden]/span/span').text
            pattern = r"(?: *)([0-9]+K*)(?: *)"
            like_count = str(likes)
            like_count = re.search(pattern, like_count).group(1)
            like_count = api_utils.prepare_reactions_to_int(like_count)
        except Exception as ex:
            like_count = None

        try:
            comments = driver.find_element(
                By.XPATH, '//div[@role="complementary"]//div/div[./div][2]//div[@role and .//i[contains(@style, "-4")]]//span').text
            comments = str(comments.replace(' comments', '').replace(' comment', ''))
            comments = api_utils.prepare_reactions_to_int(comments)
        except Exception as ex:
            comments = None
        try:
            wind_sz = driver.get_window_size()
            if post.size['height'] > wind_sz['height']:
                w = driver.execute_script('return document.body.parentNode.scrollWidth')
                driver.set_window_size(w, post.size['height'] + wind_sz['height'])
                sleep(2)
            image = post.screenshot_as_png
            featured_image = api_utils.save_byte_image(image, self.media_basedir, SmmEngine.facebook)
        except:
            pass

        social_post_reactions = self.get_detailed_reactions(driver)

        social_parsing_post = SocialParsingPostCreate(
            social_request_id=self.initial_data.social_request_id,
            link_id=self.initial_data.social_link_id,
            account_name=user_name,
            account_login=user_login,
            content=content,
            featured_image=featured_image,
            source_link=source_link,
            crawler_name="selenium-facebook-crawler-v1",
            date_of_news=post_date,
            smm_id=self.initial_data.smm_engine_id
        )

        social_post_stats = SocialPostStatCreate(
            likes=like_count,
            comments=comments
        )

        social_parsing_post.social_posts_reactions = social_post_reactions
        social_parsing_post.social_posts_stats = social_post_stats
        return social_parsing_post
    
    def extract_data_from_watch_live_page(self, driver: webdriver.Remote):
        WebDriverWait(driver, timeout=20).until(EC.visibility_of_element_located((By.XPATH, '//div[@role="main"]')))
        pass

    def extract_data_from_current_tweet_card(self, driver: webdriver.Remote):
        sleep(1)
        if "/watch/live" in driver.current_url:
            driver.find_element(By.XPATH,'//div[@role="main"]/div/div[2]/div[@class]/div[./div][1]//a[contains(@href, "video")]/ancestor::span[1]').click()
            WebDriverWait(driver, timeout=20).until(EC.visibility_of_element_located((By.XPATH, '//div[@role="main" and not(@aria-label)]')))
            return self.extract_data_from_videos_page(driver)
        elif '/watch/' in driver.current_url:
            return self.extract_data_from_watch_page(driver)
        elif '/photo' in driver.current_url:
            return self.extract_data_from_photos_page(driver)
        elif '/videos/' in driver.current_url:
            return self.extract_data_from_videos_page(driver)
        try:
            post = driver.find_element(
                By.XPATH, '(//div[@aria-describedby]//div[contains(@style,"border-radius")]/div/div[not(@*)][2])[1]')
            post_header = post.find_element(By.XPATH, './div/div/div[not(@*)][1]')
            post_content = post.find_element(By.XPATH, './div/div/div[not(@*)][2]')
            footer_content = post.find_element(
                By.XPATH, './div/div[not(@*)][3] | ./div/div[not(@*)][4]')
            WebDriverWait(driver, timeout=20).until(EC.visibility_of(post_header))

        except:
            pass
        try:
            pattern = r'(?:https:\/\/www\.facebook\.com\/)(\w+)'
            if not self.initial_data.social_link and not self.initial_data.hashtag:
                user_login = post_header.find_element(
                    By.XPATH, '(.//h3//a)[1]').get_attribute('href')
            else:
                user_login = post_header.find_element(
                    By.XPATH, '(.//h2//a)[1]').get_attribute('href')

            user_login = re.search(pattern, user_login).group(1)
        except:
            print('user_login exception')

        try:
            if not self.initial_data.social_link and not self.initial_data.hashtag:
                user_name = post_header.find_element(
                    By.XPATH, '(.//h3//a//span)[1]').text
            else:
                user_name = post_header.find_element(
                    By.XPATH, '(.//h2//a//span)[1] | (.//h2//a//span/span)[1]').text
        except:
            raise StaleElementReferenceException

        try:
            post_date = post_header.find_element(
                By.XPATH, './/div//span[@id]/span[not(@*)]//a/span | .//div//span[@id]/span[not(@*)]//a/span/span')

            sleep(1)
            post_date_image = post_date.screenshot_as_png
            text_date = self.get_text_from_image(post_date_image).strip()
            post_date = self.get_final_post_date(text_date)
        except StopIteration:
            print('Old date post')
            raise StopIteration
        except Exception as ex:
            post_date = None
            print('post_date exception')
            print(str(ex))

        try:
            driver.execute_script("window.scrollBy(0, -300)")
            post_link_hover = post_header.find_element(
                By.XPATH, './/span[@id]/span[not(@*)]//a')
            ActionChains(driver).move_to_element(post_link_hover).perform()
            driver.execute_script("window.scrollBy(0, 100)")
            ActionChains(driver).move_to_element(post_link_hover).perform()
            post_link: str = post_header.find_element(
                By.XPATH, './/span[@id]/span[not(@*)]//a').get_attribute("href")
            post_link = post_link[:post_link.find('?')]
            if post_link in self.unique_posts:
                raise exceptions.StaleElementReferenceException
        except exceptions.StaleElementReferenceException:
            raise exceptions.StaleElementReferenceException
        except Exception as ex:
            print('Exception post link')
            print(ex)

        try:
            post_content.find_element(
                By.XPATH, './/div[contains(text(), "See more")]').click()
        except:
            pass
        try:
            content_arr = []
            try:
                content_elem = post_content.find_elements(
                    By.XPATH, './/div[@data-ad-preview="message"]//div[contains(@style,"text-align")] | ./blockquote//div[contains(@style,"text-align")]')
            except:
                pass

            if not self.initial_data.social_link and self.initial_data.hashtag:
                content_elem = post_content.find_elements(By.XPATH, ".//span/div")

            for elem in content_elem:
                text = elem.text.strip()
                if text not in [" ", '\t', ""]:
                    content_arr.append(text + "\n")

            content = "".join(content_arr)
            if self.initial_data.social_link:
                if self.initial_data.hashtag and self.initial_data.hashtag.lower() not in content.lower():
                    return None
                elif self.initial_data.keyword and self.initial_data.keyword.lower() not in content.lower():
                    return None
        except Exception as ex:
            content = None
            print(str(ex))

        try:
            has_video = post_content.find_element(By.XPATH, './/video')
            if has_video and post_link not in self.unique_posts:
                video_preview = post_content.find_element(
                    By.XPATH, '(.//img)[1]').get_attribute('src')
                # video_preview = self.save_photo(video_preview)
                video_image_list = api_utils.save_image(
                    [video_preview], self.media_basedir, SmmEngine.facebook)
                if len(video_image_list) > 0:
                    video_preview = video_image_list[0]
            else:
                raise (NoSuchElementException)
        except NoSuchElementException:
            video_preview = None

        social_post_attachments = []

        try:
            featured_image = None
            if video_preview == None:
                image_source_links = []
                links_out = []
                image_links_obj = post_content.find_elements(
                    By.XPATH, './div[@id]//img')
                if len(image_links_obj) > 0 and post_link not in self.unique_posts:
                    for link in image_links_obj:
                        image_link = link.get_attribute('src')
                        image_source_links.append(image_link)
                    links_out = api_utils.save_image(
                        image_source_links, self.media_basedir, SmmEngine.facebook)
                if len(links_out) == 1:
                    featured_image = links_out[0]
                if len(links_out) > 1:
                    featured_image = links_out[0]
                    for link in links_out[1:]:
                        social_post_attachments.append(
                            SocialPostAttachmentCreate(image_path=link))
            else:
                raise (NoSuchElementException)
        except NoSuchElementException:
            featured_image = None

        try:
            footer_line = post.find_element(
                By.XPATH, "./div/div/div[not(@*)][3]/div/div/div[not(@*)]/div/div[1]/div[1] | ./div/div/div[not(@*)][4]/div/div/div/div/div[1]/div[1]")
            emojes_line = footer_line.find_element(By.XPATH, "./div[1]")
            ActionChains(driver).move_to_element(emojes_line).perform()
            sleep(2)
        except Exception as ex:
            pass

        try:
            pattern = r"(?: *)([0-9]+K*)(?: *)"
            like_count = footer_line.find_element(
                By.XPATH, ".//div//div//span[@aria-hidden]/span/span").text
            like_count = str(like_count)
            like_count = re.search(pattern, like_count).group(1)
            like_count = api_utils.prepare_reactions_to_int(like_count)
        except Exception as ex:
            like_count = None

        try:
            comments = footer_line.find_element(
                By.XPATH, './/span[contains(text(),"comment")]').text
            comments = str(comments.replace(' comments', '').replace(' comment', ''))
            comments = api_utils.prepare_reactions_to_int(comments)
        except Exception as ex:
            # print(ex)
            comments = None

        try:
            shares = footer_line.find_element(
                By.XPATH, './/span[contains(text(),"share")]').text
            shares = str(shares.replace(' shares', '').replace(' share',''))
            shares = api_utils.prepare_reactions_to_int(shares)
        except Exception as ex:
            # print(ex)
            shares = None

        social_post_reactions = self.get_detailed_reactions(driver)

        try:
            if featured_image == None:
                wind_sz = driver.get_window_size()
                if post_content.size['height'] > wind_sz['height']:
                    w = driver.execute_script('return document.body.parentNode.scrollWidth')
                    driver.set_window_size(w, post_content.size['height'] + wind_sz['height'])
                    sleep(2)
                image = post_content.screenshot_as_png
                featured_image = api_utils.save_byte_image(image, self.media_basedir, SmmEngine.facebook)
        except:
            pass

        social_parsing_post = SocialParsingPostCreate(
            social_request_id=self.initial_data.social_request_id,
            link_id=self.initial_data.social_link_id,
            account_name=user_name,
            account_login=user_login,
            content=content,
            featured_image=featured_image,
            video_image=video_preview,
            source_link=post_link,
            crawler_name="selenium-facebook-crawler-v1",
            date_of_news=post_date,
            smm_id=self.initial_data.smm_engine_id
        )

        social_post_stats = SocialPostStatCreate(
            likes=like_count,
            comments=comments,
            retweets=shares
        )

        social_parsing_post.social_posts_reactions = social_post_reactions
        social_parsing_post.social_posts_attachments = social_post_attachments
        social_parsing_post.social_posts_stats = social_post_stats
        return social_parsing_post

    def main(self):
        try:
            try:
                driver = self.create_firefox_instance()
            except Exception as ex:
                raise 
            driver.maximize_window()
            driver.get("https://www.facebook.com")
            notify.info('Facebook crawling was started')
            # driver.delete_all_cookies()
            # cookies = pickle.load(
            #     open("app/crawlers/smm_engines/facebook/cookies.pkl", "rb"))
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
                
            # # driver.refresh()
            # driver.get('https://www.facebook.com')
            # save_cookies_to_file(driver, self.active_cookie, self.initial_data.smm_engine_name, self.media_basedir,False)
            # self.login(driver)
            # sleep(1000)
            # sleep(60)
            # pickle.dump(driver.get_cookies() , open("app/crawlers/smm_engines/facebook/cookies.pkl","wb"))
            # sleep(1000)

            last_position = None
            end_of_scroll_region = False
            if self.initial_data.social_link:

                driver.get(self.initial_data.social_link)
                sleep(5)
                # driver.execute_script("window.scrollBy(0, -300)")
                print("Opened: ", self.initial_data.social_link)
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

            elif self.initial_data.keyword != "" or self.initial_data.hashtag != "":
                self.current_link = self.generate_query(self.initial_data)
                driver.get(self.current_link)
                sleep(2)
                try:
                    driver.find_element(
                        By.XPATH, '//div[@aria-label="You’re Temporarily Blocked"]//div[@aria-label="OK"]').click()
                except:
                    pass
            try:
                driver.find_element(By.XPATH, '//span[contains(text(),"No posts available")]')
                raise StopIteration
            except StopIteration:
                raise StopIteration
            except:
                pass
            try:
                driver.find_element(By.XPATH, '//span[contains(text(), "This content isn")]')
                raise StopIteration
            except StopIteration:
                raise StopIteration
            except:
                pass
            sleep(2)
            while not end_of_scroll_region:
                try:
                    posts: list[WebElement] = self.collect_all_tweets_from_current_view(driver)
                    print(len(posts))
                except:
                    raise
                if len(posts) == 0:
                    raise 
                for key, post in enumerate(posts):
                    print(key)
                    try:
                        card = post.find_element(
                            By.XPATH, './/div[@aria-describedby]//div[contains(@style,"border-radius")]/div/div[not(@*)][2]')
                        post_header = card.find_element(
                            By.XPATH, './div/div[not(@*)][1]')
                        post_link_hover = post_header.find_element(
                            By.XPATH, './/div/div[2]/div/div[2]//span[@id]/span[not(@*)]//a')
                        ActionChains(driver).move_to_element(post_link_hover).perform()
                        driver.execute_script("window.scrollBy(0, 100)")
                        # sleep(5)
                        ActionChains(driver).move_to_element(post_link_hover).perform()
                        # sleep(1)
                        post_link: str = post_header.find_element(
                            By.XPATH, './/div/div[2]/div/div[2]//span[@id]/span[not(@*)]//a').get_attribute("href")
                        if "permalink.php" not in post_link and "/photo/" not in post_link:
                            post_link = post_link[:post_link.find('?')]
                    except:
                        continue
                    if post_link is not None:
                        if post_link in self.unique_posts:
                            continue
                        original_window = driver.current_window_handle
                        current_url = driver.current_url
                        driver.switch_to.new_window('tab')
                        print(post_link)
                        driver.get(post_link)
                        WebDriverWait(driver, timeout=10).until(
                            EC.url_changes(current_url))
                        try:
                            post: SocialParsingPostCreate = self.extract_data_from_current_tweet_card(
                                driver)
                        except StaleElementReferenceException:
                            continue
                        except StopIteration:
                            raise StopIteration
                        except Exception as ex:
                            print(ex)
                        driver.close()
                        driver.switch_to.window(original_window)
                        sleep(1)
                        driver.execute_script("window.scrollBy(0, 100)")
                        # sleep(1000)
                    if not post:
                        continue
                    if post_link not in self.unique_posts:
                        self.unique_posts.add(post_link)
                        try:
                            api_utils.send_post_to_api(post=post)

                            api_utils.send_post_to_reply_link(
                                url=self.initial_data.reply_link,
                                post=post,
                                external_id=self.initial_data.external_id
                            )

                        except HTTPException as ex:
                            api_utils.delete_trash_files(self.media_basedir, post)
                            print(ex)
                            print('Not Saved')
                            pass
                    # sleep(120)
                last_position, end_of_scroll_region = self.scroll_down_page(
                    driver, last_position)
                sleep(2)
        except StopIteration:
            notify.info("Facebook crawling was finished successfully!")
            save_cookies_to_file(driver, self.active_cookie, self.initial_data.smm_engine_name, self.media_basedir)
            pickle.dump(driver.get_cookies(), open(
                "app/crawlers/smm_engines/facebook/cookies.pkl", "wb"))
            api_utils.update_social_request_last_run(
                id=self.initial_data.social_request_id)
            raise StopIteration
        except Exception as ex:
            print(str(ex))
        finally:
            change_lock_cookie_status(self.active_cookie.id, False)
            driver.quit()
