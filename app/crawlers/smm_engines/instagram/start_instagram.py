from datetime import datetime, timedelta
import json
import pickle
from random import randint
import re
from time import sleep
import os
import uuid
import zipfile
import requests
import urllib
from http.client import HTTPException

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webelement import WebElement
# from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (InvalidArgumentException,
                                        JavascriptException,
                                        WebDriverException,
                                        NoSuchCookieException,
                                        NoSuchElementException,
                                        StaleElementReferenceException,
                                        TimeoutException)

from app.crawlers.data_handlers.DataHandler import SocialTask
# from app.crawlers.data_handlers.grid_manager import get_active_grid
from app.crawlers.proxy.proxy import get_background_js, get_manifest_json
from app.schemas.social_parsing_post import SocialParsingPostCreate
from app.schemas.social_post_attachment import SocialPostAttachmentCreate
from app.schemas.social_post_stat import SocialPostStatCreate
from app.models.social_request import SocialRequest
from app.crawlers.data_handlers.utils import send_post_to_reply_link
from app.crud.crud_social_parsing_post import social_parsing_post as crud_social_parsing_post
import app.crawlers.data_handlers.utils as api_utils
from app.crawlers.smm_engines.smm_engines import SmmEngine
from app.core.config import settings
from app.services.account_logging.cookie_manager import change_lock_cookie_status, get_cookie_file, get_full_account_info, save_cookies_to_file
from app.logging.notify import notify
from app.services.imap.imap import GetLinkFromIMAP

class InstagramScraper:

    def __init__(self, data: SocialTask):
        self.initial_data = data
        self.is_private_account = False
        self.session_id = None
        self.media_basedir = self.initial_data.reply_link.host
        self.current_link = ''
        self.unique_posts = set()
        self.is_cookie_valid = True
        self.social_account, self.active_cookie, self.proxy = get_full_account_info(self.initial_data.smm_engine_id)
        self.main()

    def create_webdriver_instance(self):
        options = webdriver.ChromeOptions()
        # os.environ['DISPLAY'] = ':10.0'
        # options.add_argument("--remote-debugging-port=9230")
        options.add_argument("start-maximized")
        # options.add_argument('--disable-dev-shm-usage')
        # options.add_argument('--disable-notifications')
        # options.add_argument('--disable-popup-blocking')
        # options.add_argument('--log-level=3')
        # options.add_argument('--no-sandbox')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        preferences = {
            "webrtc.ip_handling_policy" : "disable_non_proxied_udp",
            "webrtc.multiple_routes_enabled": False,
            "webrtc.nonproxied_udp_enabled" : False
            # "enforce-webrtc-ip-permission-check": True
        }
        options.add_experimental_option("prefs", preferences)
        
        # proxy = "176.103.120.12:45989@TIORgVo8Ovn1vs0:JoQvH8jfWHdcHeS"
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
        # options.set_capability()
        # driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        
        desired_capabilities = DesiredCapabilities.CHROME
        # active_grid = get_active_grid('chrome')
        driver = webdriver.Remote(
            command_executor=settings.REMOTE_SELENIUM_GRIDS[1],
            desired_capabilities=desired_capabilities,
            options=options
        )
        return driver

    # def create_firefox_instance(self):
    #     from selenium.webdriver.firefox.options import Options
    #     options = Options()
    #     # socks, port = settings.FULL_PROXY.split(":")
    #     # options.set_preference('network.proxy.type', 1)
    #     # options.set_preference('network.proxy.socks', socks)
    #     # options.set_preference('network.proxy.socks_port', port)
    #     # options.set_preference('network.proxy.socks_remote_dns', False)
    #     options.headless = True
    #     # driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)
    #     driver = webdriver.Remote(
    #         command_executor=settings.REMOTE_SELENIUM_GRIDS[0],
    #         desired_capabilities={'browserName': 'firefox', 'javascriptEnabled': True}, options=options)
    #     return driver

    def generate_query(self, data: SocialTask):
        hashtag = data.hashtag
        link = data.social_link
        keyword = data.keyword
        if keyword and not link:
            raise StopIteration
        if link:
            return link
        elif hashtag:
            return f'https://www.instagram.com/explore/tags/{hashtag}/'

    def collect_all_tweets_from_current_view(self, driver: webdriver.Remote, lookback_limit=25):
        if self.initial_data.social_link:
            page_cards = driver.find_elements(
                By.XPATH, '//article/div/div/div/div[not(.//*[@aria-label="Pinned post icon"])]')
        elif self.initial_data.hashtag and not self.initial_data.social_link:
            page_cards = driver.find_elements(
                By.XPATH, '//div[@role="main"]/div[./div][3]/div/div/div/div/div/div/div[./div and not(@*)]')
        # print(len(page_cards))
        if len(page_cards) <= lookback_limit:
            return page_cards
        else:
            return page_cards[-lookback_limit:]

    def login(self, driver: webdriver.Remote):
        # sleep(1000)
        driver.get('https://www.instagram.com/')
        try:
            sleep(2)
            driver.find_element(
                By.XPATH, '//input[@name="username"]').send_keys(self.social_account.login)
                # lindseystafford84
                # 34jintaisenLindsey
            sleep(3)
            driver.find_element(
                By.XPATH, '//input[@name="password"]').send_keys(self.social_account.password)
            sleep(1)
            button = driver.find_element(By.XPATH, '//button[@type="submit"]')
            ActionChains(driver).move_to_element(button).click().perform()
            sleep(5)
            try:
                driver.find_element(By.XPATH, '//p[@id="slfErrorAlert"]')
                raise TimeoutException
                """CATCH FAILED AUTH"""
                """NEED TO CHANGE IP"""
            except TimeoutException:
                raise TimeoutException
            except:
                pass
            try:
                driver.find_element(By.XPATH, "//label[contains(text(), 'Email')]/div").click()
                driver.find_element(By.XPATH, "//button[contains(text(), 'Send Security Code')]").click()
                imap = GetLinkFromIMAP(self.social_account.email, self.social_account.email_password, self.initial_data.smm_engine_name)
                code = imap.get_code_from_parsed_html()
                driver.find_element(By.XPATH, "//input[@id='security_code']").send_keys(code)
                driver.find_element(By.XPATH, "//button[contains(text(), 'Submit')]").click()
            except:
                pass
            try:
                try:
                    elem = driver.find_element(By.XPATH, f'//a[contains(@href, "{self.social_account.login}")]')
                except:
                    elem = None
                if 'onetap' in driver.current_url or elem is not None:
                    notify.info('Authenticated')
                    save_cookies_to_file(driver, self.active_cookie, self.initial_data.smm_engine_name, self.media_basedir, is_cookie_valid=False)
                    try:
                        driver.find_element(By.XPATH, "//button[contains(text(), 'Turn On')]").click()
                    except:
                        pass
                else:
                    raise TimeoutException
            except TimeoutException:
                notify.error(f'Cannot login with cookie_id: {self.active_cookie.id} and user email: {self.social_account.email}')
                raise TimeoutException
        except:
            raise

    def check_is_account_private(self, driver):
        try:
            driver.find_element(
                By.XPATH, '//article//h2[text()="This Account is Private"]')
            self.is_private_account = True
            raise StopIteration
        except StopIteration:
            raise StopIteration
        except:
            pass

    def scroll_down_page(self, driver, last_position, num_seconds_to_load=2, scroll_attempt=0, max_attempts=5):
        end_of_scroll_region = False
        # driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        body = driver.find_element(By.CSS_SELECTOR, 'body')
        for _ in range(randint(2, 4)):
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

    def extract_data_from_current_tweet_card(self, post: WebElement, driver: webdriver.Remote, likes, comments, user_name, subscribers):

        WebDriverWait(driver, timeout=10).until(
            EC.visibility_of_element_located((By.XPATH, '//article')))

        notify.info(f"Current post: {driver.current_url}")
        try:
            postDate = driver.find_element(
                By.XPATH, '//article//div[@role="presentation"]/div[2]/div[2]//time')
            post_date_text = postDate.text
            post_datetime = postDate.get_attribute('datetime')
            if self.initial_data.social_link:
                if 'ago' in post_date_text.lower():
                    post_date = datetime.strptime(
                        post_datetime[:-5], '%Y-%m-%dT%H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
                else:
                    raise StopIteration

        except StopIteration:
            raise StopIteration
        except Exception as ex:
            print(ex)
            post_date = None

        try:
            user_login_link = driver.find_element(
                By.XPATH, '(//header//a)[1]').get_attribute('href')
            user_login = re.search(r'(?:.+\/)(.+)(?:\/.*)', user_login_link).group(1)
        except:
            pass

        try:
            content = None
            content_elems = []
            content_elements = driver.find_elements(
                By.XPATH, f'//article//div[@role="presentation"]//ul//a[text()="{user_login}"]/ancestor::h2/following-sibling::div[1]//h1')
            for elem in content_elements:
                content_elems.append(elem.text)
            content = "\n".join(content_elems)
            if self.initial_data.social_link:
                if self.initial_data.hashtag and self.initial_data.hashtag.lower() not in content.lower():
                    return
                elif self.initial_data.keyword and self.initial_data.keyword.lower() not in content.lower():
                    return
        except Exception as ex:
            print(ex)
            content = None
        # sleep(100)
        post_link = driver.current_url

        try:
            likeCount = api_utils.prepare_reactions_to_int(likes)
        except Exception as ex:
            print('likeCount exception')
            print(ex)
            likeCount = 0

        try:
            commentCount = api_utils.prepare_reactions_to_int(comments)
        except Exception as ex:
            print('Comment exception')
            print(ex)
            commentCount = 0

        try:
            multiple_elements = driver.find_elements(
                By.XPATH, '//article//div[contains(@class,"_acnb")]')
        except:
            multiple_elements = None

        post_attachments = []
        video_preview = None
        featured_image = None
        try:
            if not multiple_elements:
                try:
                    image_href = driver.find_element(
                        By.XPATH, '//article/div/div[1]//img').get_attribute('src')
                    if image_href:
                        # featured_image = self.save_photo(image_href)
                        featured_image_list = api_utils.save_image(
                            [image_href], self.media_basedir, SmmEngine.instagram)
                        featured_image = featured_image_list[0]
                except:
                    pass

                try:
                    video_href = driver.find_element(
                        By.XPATH, '//article/div/div[1]//video').get_attribute('src')
                    if video_href:
                        links_out = api_utils.save_video(
                                [video_href], self.media_basedir, SmmEngine.instagram)
                        post_attachments.append(
                            SocialPostAttachmentCreate(video_path=links_out[0]))
                        video_preview_href = driver.find_element(
                            By.XPATH, '//article/div/div[1]//img').get_attribute('src')
                        video_image_list = api_utils.save_image(
                            [video_preview_href], self.media_basedir, SmmEngine.instagram)
                        video_preview = video_image_list[0]
                except:
                    pass
                if featured_image == None:
                    try:
                        video_preview = driver.find_element(By.XPATH, '//div[@role="dialog"]').screenshot_as_png
                        video_preview = api_utils.save_byte_image(video_preview, self.media_basedir, SmmEngine.instagram)
                    except:
                        video_preview = None
                    
                    try:
                        image = driver.find_element(By.XPATH, '//article/div').screenshot_as_png
                        featured_image = api_utils.save_byte_image(image, self.media_basedir, SmmEngine.instagram)
                    except:
                        pass
            
            elif len(multiple_elements) > 1:
                translateX = 0
                translateX_range = driver.find_element(
                    By.XPATH, '//article/div/div[1]//ul//li[3]').get_attribute('style')
                translateX_offset = int(
                    re.search(r'(?:transform: translateX\()(\w+)(?:px\);)', translateX_range).group(1))
                for num, _ in enumerate(range(len(multiple_elements))):
                    try:
                        image_href = driver.find_element(
                            By.XPATH, f'//article/div/div[1]//ul//li[@style="transform: translateX({translateX}px);"]//img').get_attribute('src')
                        if image_href:
                            if num == 0:
                                links_out = api_utils.save_image(
                                    [image_href], self.media_basedir, SmmEngine.instagram)
                                featured_image = links_out[0]
                            else:
                                links_out = api_utils.save_image(
                                    [image_href], self.media_basedir, SmmEngine.instagram)
                                post_attachments.append(
                                    SocialPostAttachmentCreate(image_path=links_out[0]))
                    except:
                        pass
                        
                    
                    try:
                        video_href = driver.find_element(By.XPATH, f'//article/div/div[1]//ul//li[@style="transform: translateX({translateX}px);"]//video').get_attribute('src')
                        if video_href:
                            try:
                                video_preview_href = driver.find_element(By.XPATH, f'//article/div/div[1]//ul//li[@style="transform: translateX({translateX}px);"]//image').get_attribute('src')
                                links_out = api_utils.save_image(
                                        [video_preview_href], self.media_basedir, SmmEngine.instagram)
                                video_preview = links_out[0]
                            except:
                                pass
                            links_out = api_utils.save_video(
                                [video_href], self.media_basedir, SmmEngine.instagram)
                            post_attachments.append(
                                SocialPostAttachmentCreate(video_path=links_out[0]))
                    except: 
                        pass

                    translateX += translateX_offset
                    if num != len(multiple_elements) - 1:
                        driver.find_element(
                            By.XPATH, '//article//button[@aria-label="Next"]').click()
                        WebDriverWait(driver, timeout=10).until(EC.visibility_of_element_located(
                            (By.XPATH, f'//article/div/div[1]//ul//li[@style="transform: translateX({translateX}px);"]')))
        except:
            pass

        social_parsing_post = SocialParsingPostCreate(
            social_request_id=self.initial_data.social_request_id,
            link_id=self.initial_data.social_link_id,
            smm_id=self.initial_data.smm_engine_id,
            account_name=user_name,
            account_login=user_login,
            content=content,
            featured_image=featured_image,
            video_image=video_preview,
            source_link=post_link,
            crawler_name='raased-selenium-instagram-betty-v1',
            date_of_news=post_date,
            social_posts_attachments=post_attachments,
            social_posts_stats=SocialPostStatCreate(
                likes=likeCount, comments=commentCount, subscribers=subscribers)
        )
        return social_parsing_post

    def save_stories(self, driver: webdriver.Remote, user_name, user_login, subscribers) -> None:
        notify.info('Checking stories')
        WebDriverWait(driver, timeout=10).until(
            EC.visibility_of_element_located((By.XPATH, "//header")))
        sleep(2)
        try:
            driver.find_element(
                By.XPATH, '//header/div/div[@style="cursor: pointer;"]/span').click()
            is_storie = True
        except:
            is_storie = False
            pass
        # sleep(2)
        
        multiple_elements = []
        try:
            if is_storie:
                WebDriverWait(driver, timeout=10).until(
                    EC.url_contains("stories"))
                WebDriverWait(driver, timeout=10).until(
                    EC.visibility_of_element_located((By.XPATH, "//header/div[1]/div")))
                multiple_elements = driver.find_elements(
                    By.XPATH, '//header/div[1]/div')
        except:
            multiple_elements = None

        if len(multiple_elements) > 0:
            print(f'multiple_elements: {multiple_elements}')
            for num, _ in enumerate(range(len(multiple_elements))):
                
                # sleep(1)
                try:
                    WebDriverWait(driver, timeout=10).until(
                        EC.visibility_of_element_located((By.XPATH, '//header/div[2]//button[.//*[@aria-label="Pause"]]')))
                    driver.find_element(
                        By.XPATH, '//header/div[2]//button[.//*[@aria-label="Pause"]]').click()
                except:
                    pass
                # sleep(5)
                try:
                    post_date = driver.find_element(By.XPATH, '//time')
                    post_datetime = post_date.get_attribute('datetime')
                    post_date = datetime.strptime(
                        post_datetime[:-5], '%Y-%m-%dT%H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
                except:
                    post_date = None

                post_link = driver.current_url

                try:
                    image_href = driver.find_element(By.XPATH, '//img[@sizes]').get_attribute('src')
                    if image_href is not None:
                        links_out = api_utils.save_image(
                            [image_href], self.media_basedir, SmmEngine.instagram)
                        featured_image = links_out[0]
                except:
                    featured_image = None
                    pass
                post_attachments = []
                video_preview = None
                try:
                    video_href = driver.find_element(
                        By.XPATH, f'//video').get_attribute('src')
                    if video_href:
                        # video_preview = driver.find_element(By.XPATH, '//div[@role="dialog"]').screenshot_as_png
                        # video_preview = api_utils.save_byte_image(video_preview, self.media_basedir, SmmEngine.instagram)
                        # video_preview = self.save_photo(video_priview_path)
                        # video_path = self.save_video(video_href)
                        saved_video_name_list = api_utils.save_video(
                            [video_href], self.media_basedir, SmmEngine.instagram)
                        post_attachments.append(SocialPostAttachmentCreate(
                            video_path=saved_video_name_list[0]))

                except:
                    pass
                
                if featured_image == None:
                    try:
                        video_preview = driver.find_element(By.XPATH, '//div[@role="dialog"]').screenshot_as_png
                        video_preview = api_utils.save_byte_image(video_preview, self.media_basedir, SmmEngine.instagram)
                    except:
                        video_preview = None
                    
                    try:
                        image = driver.find_element(By.XPATH, '//article/div').screenshot_as_png
                        featured_image = api_utils.save_byte_image(image, self.media_basedir, SmmEngine.instagram)
                    except:
                        pass

                social_parsing_post = SocialParsingPostCreate(
                    social_request_id=self.initial_data.social_request_id,
                    link_id=self.initial_data.social_link_id,
                    smm_id=self.initial_data.smm_engine_id,
                    account_name=user_name,
                    account_login=user_login,
                    featured_image=featured_image,
                    video_image=video_preview,
                    source_link=post_link,
                    crawler_name="raased-selenium-instagram-betty-v1",
                    date_of_news=post_date,
                    social_posts_stats=SocialPostStatCreate(subscribers=subscribers),
                    social_posts_attachments=post_attachments,
                    is_storie=True
                )
                try:

                    api_utils.send_post_to_api(post=social_parsing_post)

                    api_utils.send_post_to_reply_link(
                        url=self.initial_data.reply_link,
                        post=social_parsing_post,
                        external_id=self.initial_data.external_id
                    )
                except HTTPException as ex:
                    api_utils.delete_trash_files(
                        self.media_basedir, social_parsing_post)
                    print(ex)
                    print('Not Saved')
                    pass

                if num != len(multiple_elements) - 1:
                    driver.find_element(
                        By.XPATH, '//button[@aria-label="Next"]').click()
            try:
                driver.find_element(
                    By.XPATH, '//button[@type="button" and .//*[@aria-label="Close"]]').click()
            except:
                pass

    # def collect_all_tweets_from_current_view(self, driver: webdriver.Remote, lookback_limit=9):
    #     page_cards = driver.find_elements(By.XPATH, '//article/div/div/div/div[not(.//*[@aria-label="Pinned post icon"])]')
    #     if len(page_cards) <= lookback_limit:
    #         return page_cards
    #     else:
    #         return page_cards[-lookback_limit:]
    
    def get_status(logs):
        for log in logs:
            if log['message']:
                d = json.loads(log['message'])
                try:
                    content_type = 'text/html' in d['message']['params']['response']['headers']['content-type']
                    response_received = d['message']['method'] == 'Network.responseReceived'
                    if content_type and response_received:
                        return d['message']['params']['response']['status']
                except Exception as ex:
                    print(ex)
                    pass

    def main(self):
        print('Start main')

        last_position = None
        end_of_scroll_region = False

        try:
            driver: webdriver.Remote = self.create_webdriver_instance()
            # driver: webdriver.Remote = self.create_firefox_instance()
        except Exception as ex:
            print(str(ex))
            raise
        try:
            sleep(5)
            driver.get('https://www.instagram.com/')
            driver.maximize_window()
            sleep(5)
            try:
                driver.find_element(By.XPATH, '//button[contains(text(), "Allow essential and optional")]').click()
                WebDriverWait(driver, timeout=10).until(EC.invisibility_of_element_located((By.XPATH, '//button[contains(text(), "Allow essential and optional")]')))
            except:
                pass
            try:
                # print(driver.page_source)
                select_element = driver.find_element(
                    By.XPATH, '//div//select[@class]').click()
                select_element = driver.find_element(By.XPATH, '//footer//select')
                select_object = Select(select_element).select_by_value('en')
            except:
                print('Cannot Select EN')
                pass
            # sleep(3000)
            try:
                cookies = get_cookie_file(self.active_cookie, self.media_basedir)
                # cookies = pickle.load(
                #     open("app/crawlers/smm_engines/instagram/cookies.pkl", "rb"))
                for cookie in cookies:
                    driver.add_cookie(cookie)
                notify.info("Cookies added")
                driver.refresh()
                try:
                    elem = driver.find_element(By.XPATH, f'//a[contains(@href, "{self.social_account.login}")]')
                except:
                    elem = None
                if 'onetap' in driver.current_url or elem is not None:
                    notify.info('Authenticated')
                    # save_cookies_to_file(driver, self.active_cookie, self.initial_data.smm_engine_name, self.media_basedir, is_cookie_valid=False)
                else:
                    raise InvalidArgumentException
                # try:
                #     WebDriverWait(driver, timeout=30).until(
                #         EC.visibility_of_all_elements_located((By.XPATH, '//a[@href="/"]')))
                # except:
                #     raise InvalidArgumentException
                
                # sleep(100)
            except (InvalidArgumentException, FileNotFoundError):
                self.is_cookie_valid = False
                self.login(driver)
                pickle.dump(driver.get_cookies(), open(
                    "app/crawlers/smm_engines/instagram/cookies.pkl", "wb"))
            # sleep(2)
            self.current_link = self.generate_query(self.initial_data)
            driver.get(self.current_link)
            self.session_id = driver.session_id
            notify.info(f'Current page: {self.current_link} SessionId: {self.session_id}')
            try:
                is_failed = driver.find_element(By.XPATH, '//h2[contains(text(),"Sorry, this page isn")]')
                raise StopIteration
            except StopIteration:
                raise StopIteration
            except:
                pass
            sleep(2)
            WebDriverWait(driver, timeout=10).until(
                EC.visibility_of_element_located((By.XPATH, '//article')))
            self.check_is_account_private(driver)

            followers_count = driver.find_element(
                By.XPATH, "//header//a[contains(@href,'followers')]//span").text
            try:
                followers_count = api_utils.prepare_reactions_to_int(followers_count)
            except Exception as ex:
                followers_count = 0

            try:
                user_name = driver.find_element(
                    By.XPATH, '//section/main//section/div/span[1]').text
            except:
                user_name = ''
            try:
                user_login = driver.find_element(By.XPATH, '//h2').text
            except:
                user_login = ''

            self.save_stories(driver, user_name, user_login, followers_count)
            sleep(5)
            while not end_of_scroll_region:
                try:
                    posts = self.collect_all_tweets_from_current_view(driver)
                except:
                    raise
                # print(len(posts))
                for post in posts:
                    try:
                        original_window = driver.current_window_handle
                        postLink = post.find_element(By.XPATH, './a')
                        post_link = postLink.get_attribute('href')
                        if post_link in self.unique_posts: 
                            continue
                        ActionChains(driver).move_to_element(post).perform()
                        sleep(3)
                        try:
                            like_shadow_blocks = postLink.find_elements(
                                By.XPATH, './div[@style="background: rgba(0, 0, 0, 0.3);"]/ul/li')
                        except:
                            like_shadow_blocks = []
                        if len(like_shadow_blocks) == 2:
                            likes = like_shadow_blocks[0].text
                            comments = like_shadow_blocks[1].text
                        elif len(like_shadow_blocks) == 1:
                            likes = 0
                            comments = like_shadow_blocks[0].text
                        else:
                            likes = 0
                            comments = 0

                        # print(likes)
                        # print(comments)
                        driver.switch_to.new_window('tab')
                        # print(post_link)
                        driver.get(post_link)
                        sleep(3)
                        parsing_post: SocialParsingPostCreate = self.extract_data_from_current_tweet_card(
                            post, driver, likes, comments, user_name, followers_count)
                        driver.close()
                        driver.switch_to.window(original_window)
                    except StaleElementReferenceException:
                        continue
                    except StopIteration:
                        notify.info('Old Date Post Found. Stop crawling!')
                        raise StopIteration
                    except Exception as ex:
                        print(ex)
                    if not parsing_post:
                        continue
                    post_link = parsing_post.source_link
                    if post_link not in self.unique_posts:
                        self.unique_posts.add(post_link)
                        try:
                            api_utils.send_post_to_api(post=parsing_post)

                            api_utils.send_post_to_reply_link(
                                url=self.initial_data.reply_link,
                                post=parsing_post,
                                external_id=self.initial_data.external_id
                            )

                        except HTTPException as ex:
                            api_utils.delete_trash_files(
                                self.media_basedir, parsing_post)
                            print(ex)
                            print('Not Saved')
                            pass
                last_position, end_of_scroll_region = self.scroll_down_page(
                    driver, last_position)
            raise StopIteration
        except StopIteration:
            save_cookies_to_file(driver, self.active_cookie, self.initial_data.smm_engine_name, self.media_basedir)
            pickle.dump(driver.get_cookies(), open(
                "app/crawlers/smm_engines/instagram/cookies.pkl", "wb"))
            api_utils.update_social_request_last_run(
                id=self.initial_data.social_request_id)
            raise StopIteration
        except ConnectionAbortedError:
            print('Connection Error')
            raise Exception
        except Exception as ex:
            print(str(ex))
            raise Exception
        finally:
            change_lock_cookie_status(self.active_cookie.id, False)
            driver.quit()
