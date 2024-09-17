import csv
from http.client import HTTPException
import json
import logging
import os
from requests import HTTPError
import re
from time import sleep
from typing import List
import uuid
from datetime import datetime, timedelta
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common import exceptions
from selenium.webdriver.firefox.options import Options
from tenacity import RetryError
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import parsedatetime
from tenacity import RetryError, Retrying, after_log
from app.crawlers.data_handlers.DataHandler_old import DataHandler
from app.crawlers.data_handlers.DataHandler import SocialTask
# from app.crawlers.proxy.proxy import Proxy
from fake_headers import Headers
from decouple import config
from tenacity import after_log,retry,wait_chain,wait_fixed
from tenacity import RetryError
from app.core.config import settings
from selenium.webdriver.chrome.service import Service
from app.crawlers.data_handlers.grid_manager import get_active_grid
from app.crawlers.smm_engines.smm_engines import SmmEngine
from app.schemas.social_parsing_post import SocialParsingPostCreate
from app.schemas.social_post_attachment import SocialPostAttachmentCreate
from app.schemas.social_post_stat import SocialPostStatCreate
import app.crawlers.data_handlers.utils as api_utils
from selenium.webdriver.remote.webelement import WebElement
import dateparser

# from models.SocialParsingPost import SocialParsingPost
    
class MediumScraper:
    def __init__(self, data: SocialTask):
        self.initial_data = data
        self.is_empty_page = False
        self.session_id = None
        self.media_basedir = self.initial_data.reply_link.host
        self.current_link = ''
        self.unique_posts = set()
        self.main()

    def create_webdriver_instance(self):
        try:
            options = webdriver.ChromeOptions()
            os.environ['DISPLAY'] = ':10.0'
            options.add_argument("--remote-debugging-port=9230")
            options.add_argument("start-maximized")
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-notifications')
            options.add_argument('--disable-popup-blocking')
            options.add_argument('--log-level=3')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            # options.add_argument(f'--proxy-server=http://193.218.222.18:47895')
            # driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            
            desired_capabilities = DesiredCapabilities.CHROME
            active_grid = get_active_grid('chrome')
            driver = webdriver.Remote(
                command_executor=active_grid,
                desired_capabilities=desired_capabilities,
                options=options
            )
            return driver
        except Exception as ex:
            print('Webdriver error') 
            print(str(ex))

    def create_firefox_instance(self):
        options = webdriver.FirefoxOptions()
        # socks, port = config('FULL_PROXY').split(":")
        # options.set_preference('network.proxy.type', 1)
        # options.set_preference('network.proxy.socks', socks)
        # options.set_preference('network.proxy.socks_port', port)
        # options.set_preference('network.proxy.socks_remote_dns', False)
        # options.headless = True
        desired_capabilities = DesiredCapabilities.FIREFOX
        active_grid = get_active_grid('firefox')
        driver = webdriver.Remote(
                command_executor=active_grid,
                desired_capabilities=desired_capabilities,
                options=options
            )
        return driver

    def prepare_keywords(self,keyword: str, separator: str):
        keyword = keyword.replace(' ', separator).lower()
        return keyword

    def generate_query(self, data: SocialTask) -> List[str]:
        
        queries = []
        keyword = data.keyword
        link = data.social_link
        if link:
            return [link]
        elif keyword:
            key = self.prepare_keywords(keyword, '-')
            queries.append(f'https://medium.com/tag/{key}')
            queries.append(f'https://medium.com/tag/{key}/latest')
            queries.append(f'https://medium.com/tag/{key}/top/week')
            return queries
    
    def modify_query(self, query, current_query):
        pattern = r'(?:.+)(\/\w+)$'
        prefix = re.search(pattern, query).group(1)
        return current_query + prefix

    def extract_data_from_current_post_card(self, card: webdriver.Remote, user_login: str, title: str, user_name: str, post_date: str, post_link: str) -> SocialParsingPostCreate:
        try:
            card.find_element(By.XPATH,'//div[@role="alert"]//following-sibling::div[1]//button').click()
        except:
            pass
        try:
            # card.switch_to.default_content()
            # print('start saving text')
            post_text = self.convert_card_content_to_text(card)
            # print('text recieved')
            if post_text == "Content Not Found":
                post_text = None
            if self.initial_data.social_link:
                if self.initial_data.hashtag and self.initial_data.hashtag.lower() not in post_text.lower():
                    raise StopIteration
                elif self.initial_data.keyword and self.initial_data.keyword.lower() not in post_text.lower():
                    raise StopIteration
        except StopIteration:
            raise StopIteration
        except:
            print('post text exception on page' + card.current_url)
            pass
            # raise
        post_name = re.sub('[\W]+$', '', title)
        post_name = re.sub('[\W]+', '_', post_name).lower()
        # print(post_name)
        try:
            reply_count = card.find_element(By.XPATH,'//footer/div/div/div/div/div[1]/div[2]//p/span').text
            reply_count = api_utils.prepare_reactions_to_int(reply_count)
        except:
            reply_count = 0
            
        try:
            like_count = card.find_element(By.XPATH,'//footer/div/div/div/div/div[1]/div[1]/span[2]//p/button').text
            like_count = api_utils.prepare_reactions_to_int(like_count)
        except:
            like_count = 0
            
        social_post_attachments = []

        # try:
        #     source_video = card.find_element(By.XPATH,'.//video').get_attribute('src')
        # except:
        #     source_video = ''

        # try:
        #     video_preview = card.find_element(By.XPATH,'.//video').get_attribute('poster')
        #     if video_preview != None and post_link not in self.unique_posts:
        #         saved_video_preview_name = self.save_photo(video_preview)
        #     else: 
        #         raise(exceptions.NoSuchElementException)
        # except:
        #     saved_video_preview_name = ''
        #     video_preview = ''

        try:
            featured_image = None
            links_out = []
            image_source_links = []
            image_links_obj = card.find_elements(By.XPATH,'//article//section/div/div[2]/figure//img')
            if len(image_links_obj) > 0 and post_link not in self.unique_posts:
                for link in image_links_obj:
                    image_link = link.get_attribute('src')
                    image_source_links.append(image_link)
                links_out = api_utils.save_image(
                    image_source_links, self.media_basedir, SmmEngine.medium)
            if len(links_out) == 1:
                featured_image = links_out[0]
            if len(links_out) > 1:
                featured_image = links_out[0]
                for link in links_out[1:]:
                    social_post_attachments.append(
                        SocialPostAttachmentCreate(image_path=link))
            # else: 
            #     raise(exceptions.NoSuchElementException)
        except exceptions.NoSuchElementException:
            featured_image = None

        try:
            if featured_image == None:
                cur_card = card.find_element(By.XPATH, '//section')
                wind_sz = card.get_window_size()
                h = card.execute_script('return document.body.parentNode.scrollHeight')
            
                if cur_card.size['height'] > wind_sz['height']:
                    w = card.execute_script('return document.body.parentNode.scrollWidth')
                    
                    #set to new window size
                    card.set_window_size(w, cur_card.size['height'] + wind_sz['height'])
                    image = cur_card.screenshot_as_png
                    sleep(4)
                else:
                    image = cur_card.screenshot_as_png
                featured_image = api_utils.save_byte_image(image, self.media_basedir, SmmEngine.medium)
        except:
            pass

        social_parsing_post = SocialParsingPostCreate(
            social_request_id=self.initial_data.social_request_id,
            link_id=self.initial_data.social_link_id,
            smm_id=self.initial_data.smm_engine_id,
            account_name=user_name,
            account_login=user_login,
            title=title,
            post_name=post_name,
            content=post_text,
            featured_image=featured_image,
            source_link=post_link,
            crawler_name='raased-selenium-medium-betty-v1',
            date_of_news=post_date,
            social_posts_attachments=social_post_attachments,
            social_posts_stats=SocialPostStatCreate(
                likes=like_count, comments=reply_count)
        
        ) 
        return social_parsing_post
    
    def check_for_empty_page(self, driver: webdriver.Remote, xpath):
        try:
            empty_text  = driver.find_element(By.XPATH, xpath)
        except:
            empty_text = None
            pass
        if empty_text != None:
            print('No data on page: ', driver.current_url, " SessionId: ", self.session_id)
            # self.save_error_log(driver,"No data on current page")
            self.is_empty_page = True
            raise ValueError

    def collect_all_posts_from_current_view(self,driver: webdriver.Remote, lookback_limit=20):
        """The page is continously loaded, so as you scroll down the number of tweets returned by this function will
        continue to grow. To limit the risk of 're-processing' the same tweet over and over again, you can set the
        `lookback_limit` to only process the last `x` number of tweets extracted from the page in each iteration.
        You may need to play around with this number to get something that works for you. I've set the default
        based on my computer settings and internet speed, etc..."""
        try:
            page_cards = driver.find_elements(By.XPATH, '//article[not(.//p[contains(text(), "Member-only")])]')
        except:
            return None

        print(len(page_cards))
        if len(page_cards) <= lookback_limit:
            return page_cards
        else:
            return page_cards[-lookback_limit:]
    
    def convert_date(self, date):
        return dateparser.parse(date)
        # datetime = parser.parse(date, fuzzy=True)
        # print(datetime)
        # return datetime
        constants = parsedatetime.Constants( usePyICU=False)
        cal = parsedatetime.Calendar(constants)
        time_struct, parse_status = cal.parse(date)
        return datetime(*time_struct[:6])
    
    def convert_card_content_to_text(self, card: webdriver.Remote):
        full_text = []

        try:
            card_attributes = card.find_elements(By.XPATH, '//article//section/div/*[./*]')
        except:
            print('Card attr ex')
        # print(card_attributes)
        try:
            for div in card_attributes:
                els: List[WebElement] = div.find_elements(By.XPATH, './*')
                for el in els:
                    tag_name = el.tag_name
                    # print(tag_name)
                    if tag_name == 'p':
                        try:
                            full_text.append(el.text.strip())
                        except:
                            print('Paragraph exception')
                            raise
                    elif tag_name == 'div':
                        try:
                            full_text.append(el.text.strip())
                        except:
                            print('div exception')
                            raise
                    elif tag_name == 'h2':
                        try:
                            full_text.append(el.text.strip())
                        except:
                            print('h2 exception')
                            raise
                    elif tag_name == 'h1':
                        try:
                            full_text.append(el.text.strip())
                        except:
                            print('h1 exception')
                            raise
                    elif tag_name == 'pre':
                        try:
                            full_text.append(el.text.strip())
                        except:
                            print('pre exception')
                            raise
                    elif tag_name == 'ol':
                        try:
                            els_li = el.find_elements(By.XPATH, './li')
                            full_ol = []
                            for count, li in enumerate(els_li):
                                li_text = str(count + 1) + ". " + li.text.strip()
                                full_ol.append(li_text)
                            full_text.append("\n".join(full_ol))
                        except Exception as ex:
                            print(str(ex))
                            print('ol exception')
                            raise
                    elif tag_name == 'ul':
                        try:
                            els_li = el.find_elements(By.XPATH, './li')
                            full_text.append("\n".join([li.text.strip() for li in els_li])) 
                        except:
                            print('ul exception')  
                            raise
                    elif tag_name == 'blockquote':
                        try:
                            full_text.append(el.text.strip())
                        except:
                            print('blockquote exception')
                            raise
            clear_text = '\n\n'.join(full_text)
            return clear_text
        except:

            print("Error while saving post on page " + card.current_url)
            return "Content Not Found"
            raise ValueError
        

    def scroll_down_page(self, driver, last_position, num_seconds_to_load=5, scroll_attempt=0, max_attempts=10):
        """The function will try to scroll down the page and will check the current
        and last positions as an indicator. If the current and last positions are the same after `max_attempts`
        the assumption is that the end of the scroll region has been reached and the `end_of_scroll_region`
        flag will be returned as `True`"""
        end_of_scroll_region = False
        print(last_position)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        sleep(num_seconds_to_load)
        curr_position = driver.execute_script("return window.pageYOffset;")
        print(curr_position)
        if curr_position == last_position:
            if scroll_attempt < max_attempts:
                end_of_scroll_region = True
            else:
                self.scroll_down_page(last_position, curr_position, scroll_attempt + 1)
        last_position = curr_position
        return last_position, end_of_scroll_region

    def main(self):
        try:
            driver = self.create_webdriver_instance()
        except Exception as ex:
            print(str(ex))
        try:

            queries = self.generate_query(self.initial_data)
            
            for query in queries:
                last_position = None
                end_of_scroll_region = False
                count_old_date_post = 0
                driver.get(query)
                print(query + ' opened')
                driver.refresh()
                # if query != driver.current_url:
                #     driver.get(self.modify_query(query, driver.current_url))
                #     print('Link was changed')
                driver.maximize_window()
                self.check_for_empty_page(driver, '//main//div[contains(text(), "PAGE NOT FOUND")]')
                try:
                    WebDriverWait(driver, timeout=5).until(EC.visibility_of_element_located((By.XPATH,'//article')))
                except:
                    pass
                # sleep(3)
                try:
                    while not end_of_scroll_region:
                        try:
                            cards = self.collect_all_posts_from_current_view(driver)
                            print('recieved cards')
                        except:
                            print('Cards exception')
                            raise
                        if cards:
                            for card in cards:
                                # print(card.get_attribute('innerHTML'))
                                sleep(1)
                                try:
                                    # WebDriverWait(driver, timeout=5).until(EC.visibility_of_element_located((By.XPATH,'//article')))
                                    title = card.find_element(By.XPATH, './/h2').text
                                    # print(title)
                                except:
                                    print('Title not found')
                                    title = None

                                try:
                                    if self.initial_data.social_link:
                                        pattern = r"(?:https:\/\/medium\.com\/@)(.+)(?:\?.+)*"
                                        user_login = re.search(pattern, self.initial_data.social_link).group(1)
                                    else:
                                        pattern = r"(?:https:\/\/medium\.com\/@)(.+)(?:\?.+)"
                                        user_login = card.find_element(By.XPATH, './/div[contains(@style,"flex")]//a').get_attribute('href')
                                        user_login = re.search(pattern, user_login).group(1)
                                except:
                                    print('User login exception')
                                    user_login = None

                                try:
                                    if self.initial_data.social_link:
                                        user_name = driver.find_element(By.XPATH, f'//a[contains(@href,"")]/span').text
                                    else:
                                        user_name = card.find_element(By.XPATH, './/div[contains(@style,"flex")]//a').text
                                    
                                except:
                                    print('Username exception')
                                    user_name = None
                                try:
                                    if self.initial_data.social_link:
                                        post_date = card.find_element(By.XPATH, './/span//a//p[not(.//strong)]').text.replace('·','')
                                    else:
                                        post_date = card.find_element(By.XPATH, './/div[contains(@style,"flex")]/ancestor::div[1]/following-sibling::div[1]//a//p').text.replace('·','')
                                    # if 'ago' not in post_date:
                                    #     raise StopIteration
                                    post_date = self.convert_date(post_date)
                                    datetime_limit = datetime.today()-timedelta(days=9)
                                    datetime_limit = datetime_limit.strftime('%Y-%m-%d')
                                    post_date_to_datetime = post_date.strftime('%Y-%m-%d')
                                    # print(post_date_to_datetime)
                                    # print(datetime_limit)
                                    if post_date_to_datetime < datetime_limit:
                                        count_old_date_post += 1
                                        if count_old_date_post < 4:
                                            continue
                                        else:
                                            raise StopIteration
                                    post_date = post_date.strftime("%Y-%m-%d %H:%M:%S")
                                except StopIteration:
                                    print('Old date found, starting new search')

                                    raise StopIteration
                                except Exception as ex:
                                    print('Cannot get date')
                                    print(ex)
                                    post_date = None

                                # try:
                                #     average_read_time = card.find_element(By.XPATH, './/a[@aria-label="Post Preview Reading Time"]/p/span').text
                                # except:
                                #     average_read_time = ""

                                try:
                                    pattern = r"(.+)(?:\?.+)"
                                    post_link = card.find_element(By.XPATH, './/a[@aria-label="Post Preview Title"]').get_attribute('href')
                                    post_link = re.search(pattern, post_link).group(1)
                                    # print(post_link)
                                except:
                                    post_link = None
                                    print('Post link exception')
                                    raise

                                if post_link in self.unique_posts:
                                    print('Post already exists')
                                    continue
                                
                                try:
                                    original_window = driver.current_window_handle
                                    driver.switch_to.new_window('tab')
                                    sleep(1)
                                    driver.get(post_link)
                                    # driver.refresh()
                                    # sleep(15)
                                    # driver.get('https://medium.com/illumination/elon-musks-beautifully-ugly-laugh-is-exactly-why-he-s-beloved-despite-being-a-billionaire-1fd15b5e3af4')
                                    WebDriverWait(driver, timeout=5).until(EC.visibility_of_element_located((By.XPATH,'//section')))
                                    # driver.find_element(By.XPATH, '//section').click()
                                    sleep(3)
                                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
                                    sleep(2)
                                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3*2);")
                                    sleep(2)
                                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                                    # print('Page opened')
                                    # page_source = driver.page_source
                                    # print(page_source)
                                    # driver.refresh()
                                    # print(driver.execute_script("return document.documentElement.outerHTML;"))
                                    parsing_post: SocialParsingPostCreate = self.extract_data_from_current_post_card(driver,user_login=user_login, title=title, user_name=user_name, post_date=post_date, post_link=post_link)
                                    driver.close()
                                    driver.switch_to.window(original_window)
                                except StopIteration:
                                    print('Old Post')
                                    raise StopIteration   
                                except Exception as ex:
                                    print(str(ex))
                                    raise ex

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
                        last_position, end_of_scroll_region = self.scroll_down_page(driver, last_position)
                except StopIteration:
                    continue
            print('Search finished')
            raise StopIteration
        except StopIteration:
            api_utils.update_social_request_last_run(
                id=self.initial_data.social_request_id)
            raise StopIteration
        except Exception as ex:
            print(str(ex))
            raise Exception
        finally:
            driver.quit()

    # def get_result_structure(self, tweet: SocialParsingPost) :
    #     try:
    #         return asdict(tweet)
    #     except Exception as ex:
    #         print(str(ex))

# if __name__ == "__main__":
#     # st = "写在前面\n\n我们从不同的 x 模式下，挑选了较具代表性的 10 个项目从项目背景、进度、机制及赛道定位四个维度进行了对比。由此，我们希望能从宏观的角度审视 x to earn 生态，思考 x 场景的切入角度和意义，理解 earn 模式的必要性、创新性，以及不同项目和 StepN 在经济模式上的差异化。\n\n项目对比表格\n\nX to Earn 的「X」\n\n1. x 的分类\n\n在上述表格中，列举了各个 x 模式下较具代表性的项目及其机制解读。在 Axie 的 play to earn（边玩边赚） 和 StepN 的 move to earn（边跑边赚） 模式出圈后，x 模式渐次演变成了“万物皆可赚钱” 的状态：\n\n0. 日常活动下的 eat、learn、walk、bike、sex 等；\n1. Web 2 行为模式中的 search、点赞/制作小视频等；\n2. 游戏化的contest答题、卡牌对战等。\n\n从 GameFi_Chill 总结的生态全景来看，现阶段的项目仍以 move to earn 的模式进行着探索，试图在 StepN 的目标用户中分得一杯羹。\n\n2. x 背后的逻辑/切入点\n\n从出发点来思考，x to earn 是项目方对用户某种行为的鼓励 — 吃，读书，写作，策展，交互等。很多时候项目方可能设计了一个场景而“刻意”鼓励用户去参与，但这样的激励往往很难持续也不利于增加用户粘性。项目方不妨思考一下从心理层面来说，什么才是人们愿意参与的行为：\n\n下意识的/适合嵌入日常生活的习惯：有多少人在餐馆吃饭前要先拍下食物照片呢？也许顺延着这个想法，Poppin 中的 x 就是让用户通过分享食物照片来喂养虚拟宠物的行为。bike to earn 虽然不是下意识的行为，但也是可以嵌入人们日常生活而不用额外付出时间的活动。\n成瘾的行为：与其去培养一个习惯，不如把 x 设定为一个令人“成瘾”的行为，这可能是追剧、宠物等。\n满足感/成就感：x 的场景可以和即刻的满足感结合起来，比如学习语言，答对问题等实现技能变现的平台。\n理想化的愿景：源于生活但是高于生活的愿景也是现代人所追求的，比如 Hivemapper 旨在由个体通过行车记录仪建立的去中心化地图。\n\n此外，x to earn 相比 play to earn 有着更广泛的叙事空间 — 比如 Bike to earn 类型的项目提出的碳排放变现回流经济，通过减少碳排放是的与碳排放挂钩的真实价值回流到经济体系中，亦或是通过 Hivemapper 创造的用行车记录仪“挖”出来的去中心化地图。开发者有很大的空间可以继续设想在真实生活中或是网络上可以作为 x 并且变现的行为。\n\n虽然 x to earn 的核心是 x 的行为，但是很多项目都加入了 social-Fi 的元素。在这里可以把 social-fi 的元素理解成鼓励用户增长的一种策略，同时 social 的元素也需要与 x 的行为契合从而增加用户粘性，营造一个生机勃勃的生态。比如 EyesFi 中用户可以通过互相关注和送礼物来获得代币奖励 ，或者增加智慧值从而加速代币赚取，这和 EyesFi 中鼓励的策展和点赞行为是紧密关联的。\n\nsocial 的元素还可以是“非交互式”的，而是一种单向的展示，比如 quest3.xyz 中的奖励就是一个不能交易或转让的 SBT （灵魂绑定代币）NFT，供用户记录自己的足迹，并添加了一种成就感和纪念感。\n\n但就目前的行为模式来看，x 模式并未具有颠覆意义的创新。它更多将人类日常行为再现（如 StepN 倡导的 Move），或是对现有互联网模式下娱乐成瘾类的重塑（如定位为 Web3 版Tiktok 的 Rocket Video）。\n\nX to Earn 的「Earn」\n\n1. 项目的长期运转仰仗着内部经济循环 + 外部正向收益两个方面。\n\n内部循环：游戏模式的迭代，数值的调整等\n\n将 x to earn 的核心放在 earn 行为之上，似乎并不是一个明智选择。尽管 x 模式能吸引大批受盈利驱使而来的用户尝试，但旁氏经济结构下，项目经济若想得以持续，离不开套娃式的拉新举动。而正是由于 earn，项目的币价下跌就如互联网们取消/降低了用户补贴一般，Axie Infinity 和 StepN 面临的是第二阶段的拉新和存量解决难题。而两者在增加“内部价值循环”之上，选择了不一样的策略。\n\n由于代币价格下降、Ronin 侧链遭受黑客攻击这些市场因素，再加上经济模型不完善，Axie 的 DAU 正在经历着明显的下降趋势，用户开始大规模流失。\n\nAxie Infinity 的版本迭代选择了以游戏可玩性为突破口。 2022 年 4 月 7 日，Axie 推出了新版本 Origin。新版本降低了用户门槛，新玩家可免费领取 3 个初始 Axies 进行试玩；7 月 1 日，Axie 上线的虚拟地块质押（land staking）功能。不同的土地质押可每日获得不一样的 AXS 收益，这在一定程度上，可以理解为对 earn 模式的改良，用户在游戏内的盈利方式得以扩充。\n\n而 StepN 则通过游戏数值的调整进行游戏经济（Game Economy）的升级。根据公告，StepN 的举措包括，如通过 GST 数值进行动态成本调整（Dynamic Minting Costs），增加的鞋子合成机制（The recycling mechanism of sneakers and gems），跨链能量共享（The cross-realm energy bridge）等。当然，跨链能量共享更可以理解为传统游戏的多服形式，在 Solana 和 BNB 链之后，StepN 在 7 月 16 日将开始支持以太坊，并称之为 APE Realm。BAYC 持有者将获得一个免费的 mint 鞋子的机会；也就是说，StepN 看准的不仅是以太坊生态的流量，还顺带瞄准了 NFT 蓝筹项目们本身拥有的流量，来作为开拓新用户的一次尝试。除此以外，STEPN 也选择将季度利润的 5% 来用于 GMT 回购和销毁上，减少代币供应来调整经济模型。\n\n由叙事结构的调整和合作项目带来的外部收益\n\n达到内部价值循环是一个需要持续调整的过程，与此同时，项目方还可以思考的是如何增加外部性价值。我们认为外部性价值的增长来源可以有两种：品牌营销/叙事，合作伙伴。\n\n观察 STEPN 后期在叙事和品牌营销上的调整，我们可以看到项目方逐渐的把用户的注意力转移到健康，以及通过运动而带来的人与人和人与自然的连接的觉察。此外，项目方还通过拍卖捐赠的方式来加强自身的品牌概念。\n\n此外，项目与 Web2 企业的合作也可以增加外部性价值，比如 STEPN 与 ASICS 联名推出的 NFT 跑鞋，也有用户在 STEPN 推特下留言表示希望看到和 Supreme 的联名。\n\n2. 以 “earn”为核心的项目们，在技术、运营或经济模型上都一时间并无创新\n\n整体来看，这些项目都将“earn”的模式作为项目创新性进行挖掘，但在创意度、运营模式上都并无新意。一类是 Axie/StepN 的仿盘，另一类则是简单的将链下行为/游戏/社交模式贴上了代币激励的盈利标签。这意味着对项目方来说，靠着挣钱噱头吸引来的玩家们既不能为项目赋能，亦难以对平台产生高度粘性。这样的商业模式，在互联网平台们靠补贴引发一轮轮烧钱大战之时，就已饱具争议。更重要的是，当项目方们将注意力过度放在 earn 模式上变现时，项目生态的长期性反而得到瓦解。毕竟，传统链游/互联网模式下，用户也具有着多样化的盈利方式。尽管 x to earn 打破了网络的边界，拥有着更开放、透明的经济体；但资本（如代币/NFT）更加流通之下，资本价值稳定性反而更易失衡。 earn 方式的有效性、可持续性、可变现性等都处在探索阶段。\n\n3. 欠缺热度和可挖掘深度的模式下，项目获客渠道十分有限\n\nx to earn 仍是一个“实验阶段”。当项目机制不够成熟，不够特别，不够吸引人之下，用户量少就意味着绝对劣势。以最直观的 Twitter followers 数据为例，StepN followers 约 639.6K，Axie Infinity 则有 945.4K；而图表总结的大部分项目 followers 仅为 10K 左右。可持续的盈利模式是吸引大多数用户进入游戏的第一个指标。从营销角度来看，这些 x 的模式在话题的热度和深度上都没有创新，这也意味着他们的流量天花板非常低，既无法吸引新用户进入生态，解决用户痛点，也无法维持存量客户。\n\n以 20 年开始的问答赚钱项目 PlotX 为例，尽管项目方与各大赛事建立联系，组织相关的问答竞赛，但用户始终未被抓牢，真实需求无法被满足。对于传统玩家来说，参与链上的问答游戏和互联网问答游戏并无实质区别，只是将收益由法币变成了价格具浮动的代币。我们认为，项目方常常设想了一个“伪需求”，而期待用户对其产生兴趣且参与，本末倒置。\n\nStepN 热潮退去之后一段时间或很难看得到下一个能结合“天时地利人和”的项目。\n\nx to earn 模式如何创新？\n\nx to earn 模式要想破局进入下一个阶段，势必需考虑以下几个要素：\n\n根据项目阶段，项目方需要作出的突破和创新：\n\nx to earn 在项目初期的**“激进扩张”是值得尝试的**。激进扩张的方式可能是提供一个较短的回本周期，甚至是烧钱制造足够的噱头吸引用户进行 x 的行为。比如 Paypal 在创业初期给使用者 5 美金的奖励，从而保证了日均 2% 以上的指数型增长。\n项目发展的阶段里势必会有市值收缩，筛选参与者的阶段，但这并不等同于“死亡螺旋”，Axie Infinity 的代币价格虽然跌去超过 90%，但是新增用户还是在出现，项目方在熊市里也在坚持 build， 这样看来这款游戏的公允价值就在持续的积累/被发现。\n无论是 PAKA Labs 在文中提到的那一种发展模式 — 以”氪“养“打”、以”懒“养“勤”、打卡模式、以“网”养“点”、流量变现，x to earn 需要找到可持续的经济来源，以实现第二次增长曲线。\n从宏观的角度来看，项目应围绕着 x 建立生态系统，这个生态里可能会有赞助商，广告商，交易者，收藏者，忠实粉丝，游戏者，打金者等等。通过生态内多方的生产，交换而实现一个经济体系闭环。\n\n另一方面，我们正看到一些 Web2 企业将 x to earn 作为一种全新的商业模式和营销理念，开启 Web3 探索大门。\n\nMulticoin Capital 在推出基金 Venture Fund III 的时候就指出未来将会关注 Proof of Physical Work 的概念，即利用链上的经济体制来激励链下的“可验证”的工作，从而更近一步的把链上的资本形成和人们的合作形式拓展到链下（比如 Multicoin 参投了 drive to earn 的项目）。其实这样看来 Proof of Physical work 就是 x to earn 中分类的一种，即 x 的场景发生在链下。\n\n正因为 x to earn 有趣的衔接了链下的行为和链上的经济模式，x to earn 形成了连接 Web2/ Web3 的桥梁。我们发现传统的 Web2 企业正在做出大胆的尝试，试图利用本身就有的 x 优势，利用 x to earn 的模式吸引用户，推动自身的产品迭代。\n\n由上汽、浦东新区和阿里持股的智己汽车提出“原石谷用户数据权益计划”，这个计划的玩法本质就是drive to earn，一方面用户通过授权对形式数据的收集来开采“原石”，这些累积的“原石“不仅代表着数据权益，并且可以用于兑换汽车的指定硬件，软件从带来真实回馈。另一方面对于产品来说越来越多的数据驱动着产品的迭代，此外，从品牌上来讲“让用户拥有自己产品所产生的数据权益”确实是 Web2 里从未有过的全新概念，这样的概念有助于吸引投资者，消费者等等。\n\n究其核心， x to earn 模式之中，x 是项目叙事的出发点，是项目冷启动的价值，是人类真实需求的解决方案；而 earn 是 Web3 领域能吸引用户进场的普世卖点，良性的盈利模式和稳定的经济体循环是项目长期发展的一些必要条件。earn 不该是 x 的目标；相反，无法单独剥离的 x 和 earn 应该并线进行。换言之，唯有用户可以在 x 模式中感受到乐趣和吸引力，earn 才能锦上添花，为项目长期运转提供生机。\n\n参考\n\nhttps://twitter.com/techflowpost/status/1546436418263650304?s=21&t=YZGdkEeOqM0IsgeahkjlVA\n\nhttps://www.theblockbeats.info/news/30356\n\nhttps://www.chainfeeds.xyz/feed/detail/aa1ae6d9-a3bd-4c51-8e0e-2e18654e2ce1\n\nhttps://mp.weixin.qq.com/s/Cna-IX8qtWytDXgtRsYyQg\n\nhttps://www.chaincatcher.com/article/2074725\n\nhttps://www.chaincatcher.com/article/2076194\n\nhttps://m.odaily.news/post/5180208"
#     # print(st)
#     scraper = MediumScraper()
#     scraper.main()
