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
from app.schemas.social_parsing_post import SocialParsingPostCreate
from app.schemas.social_post_attachment import SocialPostAttachmentCreate
from app.schemas.social_post_stat import SocialPostStatCreate
from app.crawlers.data_handlers.DataHandler import SocialTask
from app.core.config import settings
import app.crawlers.data_handlers.utils as api_utils
from app.crawlers.smm_engines.smm_engines import SmmEngine


class TwitterScraper:
    logging.basicConfig(level=logging.WARN,
                        filename="app/logging/TwitterScrapperLog.txt")
    logger = logging.getLogger(__name__)

    def __init__(self, data: SocialTask):
        self.initial_data = data
        self.is_empty_page = False
        self.session_id = None
        self.current_link = None
        self.useProxy = True
        self.unique_tweets = set()
        self.OS = 'Ubuntu'
        start_date = datetime.today()-timedelta(7)
        self.start_date = start_date.strftime('%Y-%m-%d')
        self.media_basedir = self.initial_data.reply_link.host
        self.main()

    def create_webdriver_instance(self):
        try:
            print('Start creating driver')
            # headers = Headers(os="windows").generate()['User-Agent']
            options = Options()
            os.environ['DISPLAY'] = ':10.0'
            options.add_argument("--remote-debugging-port=9230")
            # options.add_argument(f'--user-agent={headers}')
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

    def create_firefox_instance(self):
        from selenium.webdriver.firefox.options import Options
        options = Options()
        socks, port = settings.FULL_PROXY.split(":")
        options.set_preference('network.proxy.type', 1)
        options.set_preference('network.proxy.socks', socks)
        options.set_preference('network.proxy.socks_port', port)
        options.set_preference('network.proxy.socks_remote_dns', False)
        options.headless = True
        driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)
        # driver = webdriver.Remote(
        #     command_executor=settings.REMOTE_SELENIUM_GRID,
        #     desired_capabilities={'browserName': 'firefox', 'javascriptEnabled': True}, options=options)
        return driver

    def generate_query(self, data: SocialTask) -> str:
        print('Generating query')
        keyword = data.keyword
        link = data.social_link
        hashtag = data.hashtag
        username = None
        if link is not None:
            pattern = r'(?:https:\/\/twitter\.com\/)(\w+)'
            username = re.search(pattern, link).group(1)
        if keyword is not None:
            key = self.prepare_keywords(keyword)
        if keyword is not None and username is not None:
            return f'https://twitter.com/search?q=({key})%20(from%3A{username})%20since%3A{self.start_date}%20-filter%3Areplies&src=typed_query&f=live'
        elif keyword is not None:
            return f'https://twitter.com/search?q={key}%20since%3A{self.start_date}%20-filter%3Areplies&src=typed_query&f=live'
        elif hashtag is not None and username is not None:
            return f'https://twitter.com/search?q=(%23{hashtag})%20(from%3A{username})%20since%3A{self.start_date}%20-filter%3Areplies&src=typed_query&f=live'
        elif username is not None:
            return f'https://twitter.com/search?q=(from%3A{username})%20since%3A{self.start_date}%20-filter%3Areplies&src=typed_query&f=live'
        elif hashtag is not None:
            return f'https://twitter.com/search?q=(%23{hashtag})%20since%3A{self.start_date}%20-filter%3Areplies&src=typed_query&f=live'

    def acceptCookies(self, driver):
        try:
            driver.find_element(
                By.XPATH, '(//div[@tabindex="0" and @role="button"])[1]').click()
        except:
            pass

    def check_for_empty_page(self, driver):
        try:
            empty_text = driver.find_element(
                By.XPATH, '//div[@data-testid="empty_state_header_text"]/span')
        except:
            empty_text = None
            pass
        if empty_text != None:
            print('No data on page: ', self.current_link,
                  " SessionId: ", self.session_id)
            self.save_error_log(driver, "No data on current page")
            self.is_empty_page = True
            raise StopIteration

    def check_for_failure_page(self, driver):
        try:
            driver.find_element(By.XPATH, '//div[@id="ScriptLoadFailure"]//span').text
            driver.refresh()
        except:
            pass

    def prepare_keywords(self, keyword):
        keyword = keyword.replace(' ', '%20')
        return keyword

    def scroll_down_page(self, driver, last_position, num_seconds_to_load=2, scroll_attempt=0, max_attempts=5):
        end_of_scroll_region = False
        # driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        body = driver.find_element(By.CSS_SELECTOR, 'body')
        for _ in range(randint(1, 3)):
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

    def collect_all_tweets_from_current_view(self, driver: webdriver.Remote, lookback_limit=20):
        page_cards = driver.find_elements(By.XPATH, '//article[@data-testid="tweet"]')
        # print(len(page_cards))
        if len(page_cards) <= lookback_limit:
            return page_cards
        else:
            return page_cards[-lookback_limit:]

    def get_guid(self):
        guid_value = str(uuid.uuid4().hex)
        return guid_value

    def generate_tweet_id(self, tweet):
        pattern = r'(?:.+\/)(\d+$)'
        tweet_id = re.search(pattern, tweet).group(1)
        return tweet_id

    def extract_data_from_current_tweet_card(self, driver:webdriver.Remote, card: WebElement):

        try:
            user = card.find_element(
                By.XPATH, './/div[@data-testid="User-Names"]/div[1]//span/span').text
        except NoSuchElementException:
            user = ""
        except StaleElementReferenceException:
            return

        try:
            handle = card.find_element(
                By.XPATH, './/div[@data-testid="User-Names"]/div[2]//span').text
        except NoSuchElementException:
            handle = ""

        try:
            post_date = card.find_element(By.XPATH,'.//time').get_attribute('datetime')
            post_date_lookup = datetime.strptime(post_date[:-5], '%Y-%m-%dT%H:%M:%S')
            post_date = post_date_lookup.strftime('%Y-%m-%d %H:%M:%S')
            datetime_limit = datetime.today()-timedelta(days=7)
            datetime_limit = datetime_limit.strftime('%Y-%m-%d')
            post_date_to_datetime = post_date_lookup.strftime('%Y-%m-%d')
            if post_date_to_datetime < datetime_limit:
                raise StopIteration
        except NoSuchElementException:
            return
        except StopIteration:
            raise StopIteration
        try:
            post_link = card.find_element(
                By.XPATH, './/time/ancestor::a').get_attribute('href')
        except:
            post_link = ''
        
        if post_link in self.unique_tweets:
            raise StaleElementReferenceException

        try:
            _responding = card.find_element(
                By.XPATH, './div/div/div/div[2]/div[2]/div[2]/div[not(@aria-labelledby)]//div[@data-testid="tweetText"]').text
            tweet_text = _responding.replace("\n", ' ')
        except:
            tweet_text = ""

        try:
            reply_count = card.find_element(
                By.XPATH, './/div[@data-testid="reply"]').text
            reply_count = api_utils.prepare_reactions_to_int(reply_count)

        except:
            reply_count = 0

        try:
            retweet_count = card.find_element(
                By.XPATH, './/div[@data-testid="retweet"]').text
            retweet_count = api_utils.prepare_reactions_to_int(retweet_count)

        except:
            retweet_count = 0

        try:
            like_count = card.find_element(By.XPATH, './/div[@data-testid="like"]').text
            like_count = api_utils.prepare_reactions_to_int(like_count)

        except:
            like_count = 0

        social_post_attachments = []

        try:
            source_video = card.find_element(By.XPATH, './/video').get_attribute('src')
            saved_video_name_list = api_utils.save_video(
                [source_video], self.media_basedir, SmmEngine.twitter)
            if len(saved_video_name_list) > 0:
                saved_video_name = saved_video_name_list[0]
            else:
                saved_video_name = None
            social_post_attachments.append(SocialPostAttachmentCreate(
                video_path=saved_video_name
            ))
        except:
            saved_video_name = None

        try:
            video_image = None
            video_preview = card.find_element(
                By.XPATH, './/video').get_attribute('poster')
            if video_preview != None and post_link not in self.unique_tweets:
                video_image_list = api_utils.save_image(
                    [video_preview], self.media_basedir, SmmEngine.twitter)
                if len(video_image_list) > 0:
                    video_image = video_image_list[0]
                else:
                    video_image = None
            else:
                raise (NoSuchElementException)
        except NoSuchElementException:
            video_image = None

        try:
            featured_image = None
            image_links = []
            image_links_obj = card.find_elements(
                By.XPATH, './/div[@data-testid="tweetPhoto"]//img')
            if len(image_links_obj) > 0 and post_link not in self.unique_tweets:
                tweet_image = image_links_obj[0].get_attribute('src')
                links_out = api_utils.save_image(
                        [tweet_image], self.media_basedir, SmmEngine.twitter)
                if len(links_out) == 1:
                    featured_image = links_out[0]
                if len(image_links_obj) > 1:
                    featured_image = links_out[0]
                    for link in image_links_obj[1:]:
                        image_link = link.get_attribute('src')
                        image_links.append(image_link)
                links_out = api_utils.save_image(
                    image_links, self.media_basedir, SmmEngine.twitter)
                for link in links_out:
                    social_post_attachments.append(
                        SocialPostAttachmentCreate(image_path=link))
            else:
                raise (NoSuchElementException)
        except NoSuchElementException:
            featured_image = None
        try:
            if featured_image == None:
                original_window = driver.current_window_handle
                driver.switch_to.new_window('tab')
                driver.get(post_link)
                WebDriverWait(driver, timeout=10).until(
                    EC.visibility_of_element_located((By.XPATH, '(//article[@data-testid="tweet"])[1]')))
                card = driver.find_element(By.XPATH, '(//article[@data-testid="tweet"])[1]')
                wind_sz = driver.get_window_size()
                if card.size['height'] > wind_sz['height']:
                    w = driver.execute_script('return document.body.parentNode.scrollWidth')
                    #set to new window size
                    driver.set_window_size(w, card.size['height'] + wind_sz['height'])
                    sleep(4)
                image = card.screenshot_as_png
                featured_image = api_utils.save_byte_image(image, self.media_basedir, SmmEngine.twitter)
                driver.close()
                driver.switch_to.window(original_window)
                
        except Exception as ex:
            print(ex)
            pass
            

        social_parsing_post = SocialParsingPostCreate(
            social_request_id=self.initial_data.social_request_id,
            link_id=self.initial_data.social_link_id,
            account_name=user,
            account_login=handle,
            content=tweet_text,
            featured_image=featured_image,
            video_image=video_image,
            source_link=post_link,
            crawler_name="selenium-twitter-crawler-v1",
            date_of_news=post_date,
            smm_id=self.initial_data.smm_engine_id
        )

        social_post_stats = SocialPostStatCreate(
            likes=like_count,
            comments=reply_count,
            retweets=retweet_count
        )

        social_parsing_post.social_posts_attachments = social_post_attachments
        social_parsing_post.social_posts_stats = social_post_stats

        return social_parsing_post

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

        last_position = None
        end_of_scroll_region = False

        try:
            driver = self.create_webdriver_instance()
        except WebDriverException as ex:
            print(str(ex))
        try:
            sleep(2)
            self.current_link = self.generate_query(self.initial_data)
            driver.get(self.current_link)
            print(f"Current page: {driver.current_url} SessionId: {self.session_id}")
            driver.maximize_window()
            # driver.set_window_size(2200, 1440)
            # driver.execute_script("document.body.style.zoom='70%'")
            driver.refresh()
            sleep(1)
            self.check_for_failure_page(driver)
            sleep(2)
            self.acceptCookies(driver)
            self.check_for_empty_page(driver)

            while not end_of_scroll_region:
                try:
                    cards = self.collect_all_tweets_from_current_view(driver)
                except:
                    raise
                for card in cards:
                    try:
                        tweet: SocialParsingPostCreate = self.extract_data_from_current_tweet_card(driver,
                            card)
                    except StaleElementReferenceException:
                        continue
                    if not tweet:
                        continue
                    tweet_link = tweet.source_link

                    if tweet_link not in self.unique_tweets:
                        self.unique_tweets.add(tweet_link)
                        try:
                            api_utils.send_post_to_api(post=tweet)

                            api_utils.send_post_to_reply_link(
                                url=self.initial_data.reply_link,
                                post=tweet,
                                external_id=self.initial_data.external_id
                            )

                        except HTTPException as ex:
                            api_utils.delete_trash_files(self.media_basedir,tweet)
                            print(ex)
                            print('Not Saved')
                            pass
                    sleep(5)

                last_position, end_of_scroll_region = self.scroll_down_page(
                    driver, last_position)
            raise StopIteration

        except StopIteration:
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
            driver.quit()
