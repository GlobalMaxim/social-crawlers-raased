
from datetime import datetime, timedelta
from http.client import HTTPException
from decouple import config
from dateutil import parser
import json
import os
from time import sleep
import uuid
import requests
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import (InvalidArgumentException,
                                        JavascriptException,
                                        WebDriverException,
                                        NoSuchCookieException,
                                        NoSuchElementException,
                                        StaleElementReferenceException)
from app.core.config import settings
from app.crawlers.data_handlers.grid_manager import get_active_grid
from app.crawlers.smm_engines.smm_engines import SmmEngine
from app.schemas.social_parsing_post import SocialParsingPostCreate
from app.schemas.social_post_attachment import SocialPostAttachmentCreate
from app.schemas.social_post_stat import SocialPostStatCreate
from app.crawlers.data_handlers.DataHandler import SocialTask
import app.crawlers.data_handlers.utils as api_utils
import parsedatetime
from app.logging.notify import notify


class RedditScraper:

    def __init__(self, data: SocialTask):
        self.initial_data = data
        self.current_link = None
        self.media_basedir = self.initial_data.reply_link.host
        self.unique_posts = set()
        if data.social_link and '/r/' in data.social_link:
            self.is_subreddit = True
        else:
            self.is_subreddit = False
        self.main()

    def create_webdriver_instance(self):
        options = Options()
        # os.environ['DISPLAY'] = ':10.0'
        # options.add_argument("--no-sandbox")
        # options.add_argument("--remote-debugging-port=9230")
        options.add_argument("start-maximized")
        # options.add_argument(f'--user-agent={headers}')
        # options.add_argument('--disable-dev-shm-usage')
        # options.add_argument('--disable-notifications')
        # options.add_argument('--disable-popup-blocking')
        # options.add_argument('--log-level=3')
        # options.add_argument('--no-sandbox')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        # driver = webdriver.Chrome(service=Service(ChromeDriverManager(os_type="mac_arm64").install()), options=options)
        active_grid = get_active_grid('chrome')
        desired_capabilities = DesiredCapabilities.CHROME
        driver = webdriver.Remote(
            command_executor=active_grid,
            desired_capabilities=desired_capabilities,
            options=options
        )
        return driver
        
    def prepare_keywords(self,keyword):
        keyword = keyword.replace(' ', '%20')
        return keyword

    def generate_query(self, data: SocialTask) -> str:
        print('Generating query')

        keyword = data.keyword
        link = data.social_link
        hashtag = data.hashtag
        username = None
        subreddit = None
        if link and not self.is_subreddit:
            pattern = r'(?:https:\/\/www\.reddit\.com\/user\/)(\w+)'
            username = re.search(pattern, link).group(1)
        elif link and self.is_subreddit:
            pattern = r'(?:https:\/\/www\.reddit\.com\/r\/)(\w+)'
            subreddit = re.search(pattern, link).group(1)
        if keyword:
            key = self.prepare_keywords(keyword)
        if subreddit and keyword:
            return f'https://www.reddit.com/r/{subreddit}/search/?q={key}&restrict_sr=1&sr_nsfw=&t=week'
        elif subreddit:
            return f'https://www.reddit.com/r/{subreddit}/search/?=&t=week&sort=new'
        elif username:
            return f'https://www.reddit.com/user/{username}/submitted/'
        elif not subreddit and keyword:
            return f"https://www.reddit.com/search/?q={key}&t=week&sort=relevance"

    def collect_all_tweets_from_current_view(self, driver, lookback_limit=30):
        """The page is continously loaded, so as you scroll down the number of tweets returned by this function will
        continue to grow. To limit the risk of 're-processing' the same tweet over and over again, you can set the
        `lookback_limit` to only process the last `x` number of tweets extracted from the page in each iteration.
        You may need to play around with this number to get something that works for you. I've set the default
        based on my computer settings and internet speed, etc..."""
        path = "//div[@data-testid='post-container' and not(.//span[contains(text(),'promoted')])]"
        page_cards = driver.find_elements(By.XPATH, path)
        print(len(page_cards))
        if len(page_cards) <= lookback_limit:
            return page_cards
        else:
            return page_cards[-lookback_limit:]

    def convert_date(self, date):
        cal = parsedatetime.Calendar()
        time_struct, parse_status = cal.parse(date)
        return datetime(*time_struct[:6])

    def extract_data_from_current_tiktok_card(self, driver: webdriver.Remote):

        try:
            # print(driver.find_element(By.XPATH, '//div[@data-test-id="post-content"]//span[@data-click-id="timestamp"]').get_attribute('innerHTML'))
            post_date = driver.find_element(By.XPATH, '//div[@data-test-id="post-content"]//span[@data-click-id="timestamp"]').text
            post_date = self.convert_date(post_date)
            datetime_limit = datetime.today()-timedelta(days=7)
            datetime_limit = datetime_limit.strftime('%Y-%m-%d')
            post_date_to_datetime = post_date.strftime('%Y-%m-%d')
            if post_date_to_datetime < datetime_limit:
                raise StopIteration
            post_date = post_date.strftime('%Y-%m-%d %H:%M:%S')
        except StopIteration:
            notify.info("Old date post found")
            raise StopIteration
        except Exception as ex:
            post_date = None
            print('post_date exception')
            print(str(ex))

        try:
            username = driver.find_element(By.XPATH,'//div[@data-test-id="post-content"]//a[@data-testid="post_author_link"]').text
            username = username.replace('u/', '')
        except NoSuchElementException:
            username = None

        try:
            title = driver.find_element(
                By.XPATH, '//div[@data-test-id="post-content"]//h1').text
        except NoSuchElementException:
            title = None

        try:
            content_arr = []
            try:
                content_link = driver.find_element(
                    By.XPATH, '(//div[@data-test-id="post-content"]//a[@data-testid="outbound-link"])[1]').get_attribute('href')
                content_arr.append(content_link)
            except:
                pass
            try:
                # main_card = driver.find_element(By.XPATH, )
                content_elem = driver.find_elements(By.XPATH, '//div[@data-test-id="post-content"]//div[@data-click-id="text"]/div/p')
                for elem in content_elem:
                    text = elem.text.strip()
                    if text not in [" ", '\t', ""]:
                        content_arr.append(text + "\n")
            except:
                pass

            content = "".join(content_arr)
            if self.initial_data.social_link:
                if self.initial_data.hashtag and self.initial_data.hashtag.lower() not in content.lower():
                    return None
                elif self.initial_data.keyword and (self.initial_data.keyword.lower() not in content.lower() and self.initial_data.keyword.lower() not in title.lower()) :
                    return None
            if content == '':
                content = None
        except:
            content = None

        post_link = driver.current_url

        social_post_attachments = []

        try:
            featured_image = None
            image_source_links = []
            links_out = []
            image_links_obj = driver.find_elements(
                By.XPATH, '//div[@data-test-id="post-content"]/div[not(@data-ignore-click)][4]//img')
            if len(image_links_obj) > 0 and post_link not in self.unique_posts:
                for link in image_links_obj:
                    image_link = link.get_attribute('src')
                    image_source_links.append(image_link)
                links_out = api_utils.save_image(
                    image_source_links, self.media_basedir, SmmEngine.reddit)
            if len(links_out) == 1:
                featured_image = links_out[0]
            if len(links_out) > 1:
                featured_image = links_out[0]
                for link in links_out[1:]:
                    social_post_attachments.append(
                        SocialPostAttachmentCreate(image_path=link))
        except:
            featured_image = None

        try:
            video_image = None
            content_video = driver.find_element(
                By.XPATH, '(//div[@data-test-id="post-content"]//video)[1]').get_attribute('src')
            if content_video:
                video_image = driver.find_element(
                    By.XPATH, '(//div[@data-test-id="post-content"]//video)[1]/preceding-sibling::div').get_attribute('style')
                pattern = r'(?:\()(http.+)(?:\))'
                video_preview_url = re.search(pattern, video_image).group(1)
                links_out = api_utils.save_image(
                    [video_preview_url], self.media_basedir, SmmEngine.reddit)
                video_image = links_out[0]

        except:
            video_image = None

        try:
            content_gif_obj = driver.find_elements(
                By.XPATH, '(//div[@data-test-id="post-content"]//video)[1]/source')
            gif_links = []
            for gif_obj in content_gif_obj:
                gif_links.append(gif_obj.get_attribute('src'))
            links_out = api_utils.save_video(
                gif_links, self.media_basedir, SmmEngine.reddit)
            for link in links_out:
                social_post_attachments.append(
                    SocialPostAttachmentCreate(video_path=link))
        except:
            pass

        try:
            commentCount = driver.find_element(By.XPATH,'//div[@data-test-id="post-content"]//span[contains(text(), "comment")]').text.lower()
            commentCount = commentCount.split()[0]
            commentCount = api_utils.prepare_reactions_to_int(commentCount)
        except:
            commentCount = 0

        try:
            upvotesCount = driver.find_element(
                By.XPATH, '//div[@data-test-id="post-content"]//div[contains(@id, "vote-arrows")]/div').text
            if upvotesCount == "Vote":
                raise
            upvotesCount = api_utils.prepare_reactions_to_int(upvotesCount)
        except:
            upvotesCount = 0

        try:
            if featured_image == None:
                card = driver.find_element(By.XPATH, '//div[@data-testid="post-container"]')
                wind_sz = driver.get_window_size()
                h = driver.execute_script('return document.body.parentNode.scrollHeight')
            
                if card.size['height'] > wind_sz['height']:
                    w = driver.execute_script('return document.body.parentNode.scrollWidth')
                    
                    #set to new window size
                    driver.set_window_size(w, card.size['height'] + wind_sz['height'])
                    image = card.screenshot_as_png
                    sleep(4)
                else:
                    image = card.screenshot_as_png
                featured_image = api_utils.save_byte_image(image, self.media_basedir, SmmEngine.reddit)
        except:
            pass

        social_post_stats = SocialPostStatCreate(
            likes=upvotesCount,
            comments=commentCount
        )

        parsing_post = SocialParsingPostCreate(
            social_request_id=self.initial_data.social_request_id,
            link_id=self.initial_data.social_link_id,
            smm_id=self.initial_data.smm_engine_id,
            account_login=username,
            title=title,
            content=content,
            featured_image=featured_image,
            video_image=video_image,
            source_link=post_link,
            crawler_name='selenium-reddit-crawler-v1',
            date_of_news=post_date,
            social_post_attachments=social_post_attachments,
            social_posts_stats=social_post_stats,
        )
        return parsing_post

    def scroll_down_page(self, driver, last_position, num_seconds_to_load=3, scroll_attempt=0, max_attempts=5):
        """The function will try to scroll down the page and will check the current
        and last positions as an indicator. If the current and last positions are the same after `max_attempts`
        the assumption is that the end of the scroll region has been reached and the `end_of_scroll_region`
        flag will be returned as `True`"""
        end_of_scroll_region = False
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        sleep(num_seconds_to_load)
        curr_position = driver.execute_script("return window.pageYOffset;")
        print(last_position, curr_position)
        if curr_position == last_position:
            if scroll_attempt < max_attempts:
                end_of_scroll_region = True
            else:
                self.scroll_down_page(last_position, curr_position, scroll_attempt + 1)
        last_position = curr_position
        return last_position, end_of_scroll_region

    def main(self):
        end_of_scroll_region = False
        last_position = None
        try:
            driver = self.create_webdriver_instance()
        except Exception as ex:
            print(str(ex))

        self.current_link = self.generate_query(self.initial_data)
        driver.maximize_window()
        # driver.maximize_window()
        driver.get(self.current_link)
        notify.info(f"Current page: {self.current_link}")
        try:
            driver.find_element(By.XPATH, '//section/form//button[contains(text(), "Accept all")]').click()
        except:
            pass

        # try:
        #     button = driver.find_element(
        #         By.XPATH, '//div[@id="AppRouter-main-content"]//button[contains(text(), "Posts")]')
        #     if button:
        #         driver.find_element(
        #             By.XPATH, '//div[@id="AppRouter-main-content"]//button[contains(text(), "Posts")]').click()
        # except:
        #     pass

        try:
            while not end_of_scroll_region:
                WebDriverWait(driver, timeout=4).until(EC.visibility_of_all_elements_located(
                    (By.XPATH, "//div[@data-testid='post-container' and not(.//span[contains(text(),'promoted')])]")))
                cards = self.collect_all_tweets_from_current_view(driver)
                for card in cards:
                    try:
                        original_window = driver.current_window_handle
                        postLink = card.find_element(
                            By.XPATH, './/a[.//h3]').get_attribute('href')
                        if postLink in self.unique_posts:
                            continue
                        driver.switch_to.new_window('tab')
                        driver.get(postLink)
                        WebDriverWait(driver, timeout=4).until(EC.visibility_of_element_located(
                            (By.XPATH, '//div[@data-test-id="post-content"]')))
                        try:
                            driver.find_element(By.XPATH, "//button[contains(text(), 'Accept all')]").click()
                        except:
                            pass
                        post: SocialParsingPostCreate = self.extract_data_from_current_tiktok_card(
                            driver)
                        driver.close()
                        driver.switch_to.window(original_window)
                    except StaleElementReferenceException:
                        continue
                    if not post:
                        continue
                    post_link = post.source_link
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
