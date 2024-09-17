from http.client import HTTPException
import csv
import json
import os
import random
import re
from time import sleep
import uuid
import zipfile
from datetime import datetime, timedelta

from decouple import config
from dateutil import parser
import pickle
import requests
import urllib.request
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common import exceptions
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import (InvalidArgumentException,
                                        JavascriptException,
                                        WebDriverException,
                                        NoSuchCookieException,
                                        TimeoutException,
                                        NoSuchElementException,
                                        StaleElementReferenceException)

from app.crawlers.data_handlers.DataHandler import SocialTask
from app.crawlers.proxy.proxy import get_background_js, get_manifest_json
from app.schemas.social_parsing_post import SocialParsingPostCreate
from app.schemas.social_post_attachment import SocialPostAttachmentCreate
from app.schemas.social_post_stat import SocialPostStatCreate
from app.schemas.social_post_request import SocialPostRequestCreate
from app.crud.crud_social_parsing_post import social_parsing_post as crud_social_parsing_post
from app.models.social_request import SocialRequest
from app.crud.crud_social_request import social_request as crud_social_request

from app.crawlers.smm_engines.smm_engines import SmmEngine
from app.crawlers.data_handlers.utils import send_post_to_reply_link
import app.crawlers.data_handlers.utils as api_utils
from app.crawlers.data_handlers.grid_manager import get_active_grid
from app.core.config import settings
from app.services.account_logging.cookie_manager import change_lock_cookie_status, get_cookie_file, get_full_account_info, save_cookies_to_file
from app.logging.notify import notify

class TiktokScraper:

    def __init__(self, data: SocialTask):
        self.unique_posts = set()
        self.initial_data = data
        self.media_basedir = self.initial_data.reply_link.host
        self.social_account, self.active_cookie, self.proxy = get_full_account_info(self.initial_data.smm_engine_id)
        self.main()

    def create_webdriver_instance(self):
        options = Options()
        # os.environ['DISPLAY'] = ':10.0'
        options.add_argument("start-maximized")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--disable-blink-features=AutomationControlled')
        # options.add_argument("--headless")
        options.add_argument('log-level=3')
        preferences = {
            "webrtc.ip_handling_policy" : "disable_non_proxied_udp",
            "webrtc.multiple_routes_enabled": False,
            "webrtc.nonproxied_udp_enabled" : False
            # "enforce-webrtc-ip-permission-check": True
        }
        options.add_experimental_option("prefs", preferences)
        # driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        # active_grid = get_active_grid('chrome')
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
            options.add_argument(f'--proxy-server=http://{self.proxy.ip.exploded}:{str(self.proxy.port)}')
        desired_capabilities = DesiredCapabilities.CHROME
        driver = webdriver.Remote(
            command_executor=settings.REMOTE_SELENIUM_GRIDS[2],
            desired_capabilities=desired_capabilities,
            options=options
        )
        return driver

    def prepare_keywords(self, keyword):
        keyword = keyword.replace(' ', '%20').lower()
        return keyword

    def generate_query(self, data: SocialTask):
        print('Generating query')
        keyword = data.keyword
        hashtag = data.hashtag
        link = data.social_link
        username = ""
        if link != "":
            pattern = r'(?:https:\/\/www\.tiktok\.com\/@)([\w|\.]+)'
            username = re.search(pattern, link).group(1)
        if keyword:
            key = self.prepare_keywords(keyword)
        if username != "":
            return f'https://www.tiktok.com/@{username}?lang=en'
        elif keyword != "":
            return f'https://www.tiktok.com/search/video?lang=en&q={key}'
        elif hashtag != "":
            return f'https://www.tiktok.com/search/video?lang=en&q=%23{hashtag}'

    def convert_date(self, date):
        return parser.parse(date, fuzzy=True).strftime('%Y-%m-%dT%H:%M:%S')

    def collect_all_tweets_from_current_view(self, driver, lookback_limit=30):
        if self.initial_data.social_link != "":
            path = '//div[@data-e2e="user-post-item-list"]/div'
        elif self.initial_data.keyword != "" or self.initial_data.hashtag != "":
            path = '//div[@data-e2e="search_video-item-list"]/div'
            lookback_limit = 20
        page_cards = driver.find_elements(By.XPATH, path)
        if len(page_cards) <= lookback_limit:
            return page_cards
        else:
            return page_cards[-lookback_limit:]

    def extract_data_from_current_tiktok_card(self, driver: webdriver.Remote, subscribers):
        try:
            postDate = driver.find_element(
                By.XPATH, '//span[@data-e2e="browser-nickname"]/span[not(@class) and not(@style)]').text
            if self.initial_data.social_link:
                if 'd ago' in postDate:
                    days = int(postDate.replace('d ago', '').strip())
                    post_date = datetime.today()-timedelta(days=days)
                    post_date = post_date.strftime('%Y-%m-%d %H:%M:%S')
                if 'w ago' in postDate:
                    post_date = datetime.today()-timedelta(7)
                    post_date = post_date.strftime('%Y-%m-%d %H:%M:%S')
                if 'm ago' in postDate:
                    min = int(postDate.replace('m ago', '').strip())
                    post_date = datetime.today()-timedelta(minutes=min)
                    post_date = post_date.strftime('%Y-%m-%d %H:%M:%S')
                if 'h ago' in postDate:
                    hours = int(postDate.replace('h ago', '').strip())
                    post_date = datetime.today()-timedelta(hours=hours)
                    post_date = post_date.strftime('%Y-%m-%d %H:%M:%S')
                if 'ago' not in postDate:
                    raise StopIteration
            else:
                if 'd ago' in postDate:
                    days = int(postDate.replace('d ago', ''))
                    post_date = datetime.today()-timedelta(days)
                    post_date = post_date.strftime('%Y-%m-%d %H:%M:%S')
                elif 'w ago' in postDate:
                    post_date = datetime.today()-timedelta(7)
                    post_date = post_date.strftime('%Y-%m-%d %H:%M:%S')
                elif 'm ago' in postDate:
                    min = int(postDate.replace('m ago', ''))
                    post_date = datetime.today()-timedelta(minutes=min)
                    post_date = post_date.strftime('%Y-%m-%d %H:%M:%S')
                elif 'h ago' in postDate:
                    hours = int(postDate.replace('h ago', ''))
                    post_date = datetime.today()-timedelta(hours=hours)
                    post_date = post_date.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    post_date = self.convert_date(postDate)

        except StopIteration:
            raise StopIteration
        except Exception as ex:
            print(ex)
            post_date = None

        try:
            title = driver.find_element(
                By.XPATH, '//div[@data-e2e="browse-video-desc"]').text
            if self.initial_data.social_link:
                if self.initial_data.hashtag and self.initial_data.hashtag.lower() not in title.lower():
                    return
                elif self.initial_data.keyword and self.initial_data.keyword.lower() not in title.lower():
                    return
        except Exception as ex:
            print(ex)
            title = ""

        post_link = driver.current_url

        try:
            user_login = driver.find_element(
                By.XPATH, '//span[@data-e2e="browse-username"]').text
        except exceptions.NoSuchElementException:
            user_login = ''
        social_post_attachments = []
        try:
            video_preview = driver.find_element(
                By.XPATH, "//div[contains(@class,'DivContainer')]/img[contains(@class,'tiktok')]").get_attribute('src')
            video_image_list = api_utils.save_image(
                [video_preview], self.media_basedir, SmmEngine.tiktok)
            if len(video_image_list) > 0:
                video_preview = video_image_list[0]
            else:
                raise (NoSuchElementException)
        except NoSuchElementException:
            video_preview = None

        try:
            source_video = driver.find_element(
                By.XPATH, "//div[contains(@class,'DivContainer')]//video").get_attribute('src')
            # video_name = self.save_video(video_path)
            saved_video_name_list = api_utils.save_video(
                [source_video], self.media_basedir, SmmEngine.tiktok)
            if len(saved_video_name_list) > 0:
                saved_video_name = saved_video_name_list[0]
                social_post_attachments.append(SocialPostAttachmentCreate(
                    video_path=saved_video_name
                ))
            else:
                saved_video_name = None

        except:
            saved_video_name = None

        try:
            user_name = driver.find_element(
                By.XPATH, '//span[@data-e2e="browser-nickname"]').text.split('·')[0].strip()
        except Exception as ex:
            print(ex)
            user_name = ''

        try:
            likeCount = driver.find_element(
                By.XPATH, '//strong[@data-e2e="like-count"]').text
            likeCount = api_utils.prepare_reactions_to_int(likeCount)

        except Exception as ex:
            print('likeCount exception')
            print(ex)
            print(likeCount)
            likeCount = 0

        try:
            comment_сount = driver.find_element(
                By.XPATH, '//strong[@data-e2e="comment-count"]').text
            commentCount = api_utils.prepare_reactions_to_int(comment_сount)
        except Exception as ex:
            print('Comment exception')
            print(ex)
            commentCount = 0

        try:
            share_сount = driver.find_element(
                By.XPATH, '//strong[@data-e2e="share-count"]').text
            if 'Share' in share_сount:
                reply_count = 0
            else:
                reply_count = api_utils.prepare_reactions_to_int(share_сount)
        except Exception as ex:
            print('shareCount exception')
            print(ex)
            reply_count = 0
        try:
            subscribers = api_utils.prepare_reactions_to_int(subscribers)
        except Exception as ex:
            print('shareCount exception')
            print(ex)
            subscribers = 0

        try:
            current_card = driver.find_element(By.XPATH, '//div[contains(@class, "DivMainContainer")]//div[contains(@class,"DivPlayerContainer")]')
            wind_sz = driver.get_window_size()
            if current_card.size['height'] > wind_sz['height']:
                w = driver.execute_script('return document.body.parentNode.scrollWidth')
                #set to new window size
                driver.set_window_size(w, current_card.size['height'] + wind_sz['height'])
                sleep(1)
            image = current_card.screenshot_as_png
            featured_image = api_utils.save_byte_image(image, self.media_basedir, SmmEngine.tiktok)
        except:
            pass

        social_post_stats = SocialPostStatCreate(
            likes=likeCount,
            comments=commentCount,
            retweets=reply_count
        )

        social_parsing_post = SocialParsingPostCreate(
            social_request_id=self.initial_data.social_request_id,
            link_id=self.initial_data.social_link_id,
            smm_id=self.initial_data.smm_engine_id,
            content=title,
            featured_image=featured_image,
            video_image=video_preview,
            source_link=post_link,
            date_of_news=post_date,
            account_name=user_name,
            account_login=user_login,
            crawler_name='raased-selenium-tiktok-betty-v1',

        )
        social_parsing_post.social_posts_attachments = social_post_attachments
        social_parsing_post.social_posts_stats = social_post_stats

        return social_parsing_post

    def scroll_down_page(self, driver, last_position, num_seconds_to_load=3, scroll_attempt=0, max_attempts=5):
        end_of_scroll_region = False
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        sleep(num_seconds_to_load)
        curr_position = driver.execute_script("return window.pageYOffset;")
        # print(last_position, curr_position)
        if curr_position == last_position:
            if scroll_attempt < max_attempts:
                end_of_scroll_region = True
            else:
                self.scroll_down_page(last_position, curr_position, scroll_attempt + 1)
        last_position = curr_position
        return last_position, end_of_scroll_region
    
    def login(self, driver: webdriver.Remote):
        try:
            driver.get("https://www.tiktok.com/login/phone-or-email/email")
            # WebDriverWait(driver, timeout=5).until(EC.visibility_of_element_located(
            #             (By.XPATH, '//button[@data-e2e="top-login-button"]')))
            # driver.find_element(By.XPATH, '//button[@data-e2e="top-login-button"]').click()
            # WebDriverWait(driver, timeout=5).until(EC.visibility_of_element_located(
            #                 (By.XPATH, '//div[@data-e2e="login-modal"]')))
            # driver.find_element(By.XPATH, '//div[@data-e2e="channel-item" and ./ancestor::a[contains(@href, "phone")]]').click()
            # WebDriverWait(driver, timeout=5).until(EC.visibility_of_element_located(
            #                 (By.XPATH, '//div[@aria-labelledby="login-modal-title"]')))
            # driver.find_element(By.XPATH, '//a[contains(@href, "/email")]').click()
            WebDriverWait(driver, timeout=5).until(EC.visibility_of_element_located(
                        (By.XPATH, '//div[@id="loginContainer"]')))
            for i in self.social_account.email:
                driver.find_element(By.XPATH, '//input[@name="username"]').send_keys(i)
                sleep(random.uniform(0.1, 1.5))
            for i in self.social_account.password:
                driver.find_element(By.XPATH, '//input[@type="password"]').send_keys(i)
                sleep(random.uniform(0.1, 1.5))
            driver.find_element(By.XPATH, '//button[@data-e2e="login-button"]').click()
            WebDriverWait(driver, timeout=100).until(EC.visibility_of_element_located(
                            (By.XPATH, 'id="//div[@data-e2e="profile-icon"]"')))
            save_cookies_to_file(driver, self.active_cookie, self.initial_data.smm_engine_name, self.media_basedir, is_cookie_valid=False)
            notify.info("Successfully logged in!")
        except TimeoutException:
            notify.error(f'Cannot login with cookie_id: {self.active_cookie.id} and user email: {self.social_account.email}')
            raise TimeoutException
        
    def main(self):
        try:
            end_of_scroll_region = False
            last_position = None
            try:
                driver = self.create_webdriver_instance()
            except Exception as ex:
                print(str(ex))
            driver.maximize_window()

            self.initial_link = self.generate_query(self.initial_data)
            driver.get(self.initial_link)
            # sleep(1000)
            # cookies = pickle.load(open("app/crawlers/smm_engines/tiktok/cookies.pkl", "rb"))
            # for cookie in cookies:
            #     driver.add_cookie(cookie)
            try:
                el = driver.execute_script("""return document.querySelector("tiktok-cookie-banner").shadowRoot.querySelector("div.button-wrapper").querySelectorAll("button")[1]""")
                el.click()
                # driver.find_element(By.XPATH, "//button[contains(text(), 'Accept all')]").click()
            except:
                pass
            try:
                cookies = get_cookie_file(self.active_cookie, self.media_basedir)
                for cookie in cookies:
                    driver.add_cookie(cookie)
                notify.info("Cookies added")
                driver.refresh()
                try:
                    elem = driver.find_element(By.XPATH, f'//div[@data-e2e="profile-icon"]')
                except:
                    elem = None
                if elem is not None:
                    notify.info('Authenticated with cookies!')
                    # save_cookies_to_file(driver, self.active_cookie, self.initial_data.smm_engine_name, self.media_basedir, is_cookie_valid=False)
                else:
                    raise InvalidArgumentException
            except (InvalidArgumentException, FileNotFoundError):
                self.is_cookie_valid = False
                self.login(driver)
            driver.refresh()
            sleep(3)
        # pickle.dump( driver.get_cookies() , open("app/crawlers/smm_engines/tiktok/cookies.pkl","wb"))
        
            while not end_of_scroll_region:
                # sleep(1000)
                if self.initial_data.social_link != "":
                    WebDriverWait(driver, timeout=5).until(EC.visibility_of_element_located(
                        (By.XPATH, '//div[@data-e2e="user-post-item-list"]')))
                    try:
                        subscribers = driver.find_element(
                            By.XPATH, '//div[@data-e2e="user-page"]//span[@data-e2e="followers"]/preceding-sibling::strong').text
                    except:
                        subscribers = None
                elif self.initial_data.keyword != "" or self.initial_data.hashtag != "":
                    WebDriverWait(driver, timeout=5).until(EC.visibility_of_element_located(
                        (By.XPATH, '//div[@data-e2e="search_video-item-list"]')))
                cards = self.collect_all_tweets_from_current_view(driver)

                # print(driver.current_url)
                for card in cards:
                    try:
                        original_window = driver.current_window_handle
                        postLink = card.find_element(
                            By.XPATH, './/div[contains(@class, "Wrapper")]/a').get_attribute('href')
                        if postLink in self.unique_posts:
                            continue
                        driver.switch_to.new_window('tab')
                        print(postLink)
                        driver.get(postLink)
                        WebDriverWait(driver, timeout=3).until(EC.visibility_of_element_located(
                            (By.XPATH, '//div[contains(@class, "VideoContainer")]')))
                        post = self.extract_data_from_current_tiktok_card(
                            driver, subscribers)
                        driver.close()
                        driver.switch_to.window(original_window)
                    except StopIteration:
                        print('Old video')
                        raise StopIteration
                    except exceptions.StaleElementReferenceException:
                        continue
                    if not post:
                        continue
                    if postLink not in self.unique_posts:
                        self.unique_posts.add(postLink)
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

                    if len(self.unique_posts) > 20:
                        print('Finished')
                        raise StopIteration
                sleep(10)
                try:
                    driver.find_element(
                        By.XPATH, '//button[@*="search-load-more"]').click()
                except Exception as ex:
                    print(str(ex))
                    pass
                pickle.dump(driver.get_cookies(), open(
                    "app/crawlers/smm_engines/tiktok/cookies.pkl", "wb"))
                sleep(2)
                last_position, end_of_scroll_region = self.scroll_down_page(
                    driver, last_position)
            raise StopIteration
        except StopIteration:
            pickle.dump(driver.get_cookies(), open(
                "app/crawlers/smm_engines/tiktok/cookies.pkl", "wb"))
            api_utils.update_social_request_last_run(
                id=self.initial_data.social_request_id)
            raise StopIteration
        except Exception as ex:
            print(str(ex))
        finally:
            change_lock_cookie_status(self.active_cookie.id, False)
            driver.quit()
