import logging
import threading
from time import sleep
from queue import Empty, Queue
from app.core.config import settings
from app.crawlers.data_handlers.DataHandler import DataHandler
from app.crawlers.smm_engines.facebook.profile_facebook_scrapper import ProfileFacebookScraper
from app.crawlers.smm_engines.twitter.profile_twitter_scrapper import ProfileTwitterScraper
from app.schemas.profile_task import ProfileTask
from app.crawlers.smm_engines.smm_engines import SmmEngine
from app.logging.notify import notify
import app.crawlers.data_handlers.utils as api_utils


def get_data_from_db():
    data_handler = DataHandler()
    active_requests = data_handler.get_active_profile_requests_from_db()
    active_tasks = data_handler.create_profile_task_manager(
        profile_requests=active_requests)
    # print(active_tasks)
    create_task_threading(active_tasks)


def create_task_threading(active_tasks: list[ProfileTask]):
    queue = Queue()  # создаем очередь
    for i in active_tasks:
        queue.put(i)
    for _ in range(settings.CRAWLERS_MAX_THREADS):
        t = threading.Thread(target=repeat, args=(queue,))  # создаем нить
        t.start()
        sleep(2)
    queue.join()

def get_data_from_crawlers(task: ProfileTask):
    current_task = task.copy()
    new_data = ProfileTask(profile_request_id=task.profile_request_id, external_id=task.external_id,reply_link=task.reply_link)
    for smm_link in current_task.social_links:
        if smm_link.smm_slug == "twitter":
            current_task, new_data = ProfileTwitterScraper(smm_link.link, current_task, new_data).get_data()
        elif smm_link.smm_slug == "facebook":
            current_task, new_data = ProfileFacebookScraper(smm_link.link, current_task, new_data).get_data()
    new_data_ready_to_send = DataHandler().prepare_profile_data_to_send_structure(new_data)
    api_utils.append_profile_post(new_data.profile_request_id, new_data_ready_to_send)
    api_utils.send_profile_to_reply_link(new_data_ready_to_send)

def repeat(queue: Queue):
    while True:
        notify.info(f"Task queue size: {queue.qsize()}")
        try:
            task: ProfileTask = queue.get_nowait()  # ждём данные
            sleep(1)
        except Empty:
            break
        try:
            get_data_from_crawlers(task=task)
            queue.task_done()
        except StopIteration:
            queue.task_done()
            continue
        except:
            queue.put_nowait(task)
            notify.warning(f"Added task with social_request_id {task.profile_request_id} to Queue for Retry")
