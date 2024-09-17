import logging
import threading
from time import sleep
from queue import Empty, Queue
from app.core.config import settings
from app.crawlers.data_handlers.DataHandler import DataHandler
from app.schemas.social_task import SocialTask
from app.crawlers.smm_engines.smm_engines import SmmEngine
from app.crawlers.smm_engines.twitter.start_twitter import TwitterScraper
from app.crawlers.smm_engines.facebook.start_facebook import FacebookScraper
from app.crawlers.smm_engines.medium.start_medium import MediumScraper
from app.crawlers.smm_engines.tiktok.start_tiktok import TiktokScraper
from app.crawlers.smm_engines.instagram.start_instagram import InstagramScraper
from app.crawlers.smm_engines.reddit.start_reddit import RedditScraper
from app.logging.notify import notify


def get_data_from_db(smm_engine: SmmEngine):
    data_handler = DataHandler()
    smm_id = smm_engine.value
    active_requests = data_handler.get_initial_data(smm_id=smm_id)
    active_tasks = data_handler.create_task_manager(
        requests=active_requests, smm_id=smm_id)
    create_task_threading(active_tasks, smm_engine)


def create_task_threading(active_tasks: list[SocialTask], smm_engine: SmmEngine):
    queue = Queue()  # создаем очередь
    # logging.basicConfig(level=logging.WARN,
    #                     filename="app/crawlers/logging/TwitterScrapperLog.txt")
    # logger = logging.getLogger(__name__)

    for i in active_tasks:
        queue.put(i)
    for _ in range(settings.CRAWLERS_MAX_THREADS):
        t = threading.Thread(target=repeat, args=(queue, smm_engine))  # создаем нить
        t.start()
        sleep(2)
    queue.join()


def select_scraper(smm_engine: SmmEngine, task: SocialTask):
    match smm_engine:
        case smm_engine.twitter:
            TwitterScraper(task)
        case smm_engine.facebook:
            FacebookScraper(task)
        case smm_engine.tiktok:
            TiktokScraper(task)
        case smm_engine.medium:
            MediumScraper(task)
        case smm_engine.instagram:
            InstagramScraper(task)
        case smm_engine.reddit:
            RedditScraper(task)


def repeat(queue: Queue, smm_engine: SmmEngine):
    while True:
        notify.info(f"Task queue size: {queue.qsize()}", symbol=f'{smm_engine} *')
        try:
            task: SocialTask = queue.get_nowait()  # ждём данные
            sleep(1)
        except Empty:
            break
        try:
            select_scraper(smm_engine=smm_engine, task=task)
            queue.task_done()
        except StopIteration:
            queue.task_done()
            continue
        except:
            queue.put_nowait(task)
            notify.warning(f"Added task with social_request_id {task.social_request_id} to Queue for Retry")
