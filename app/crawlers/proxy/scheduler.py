import time
import logging
import aioschedule
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from multiprocessing import Queue, Process
from threading import Thread
from .worker import Worker
from .providers import *
from .providers.base_provider import BaseProvider


class Scheduler(object):

    def __init__(self):
        self.worker_queue = Queue()
        self.validator_queue = Queue()
        self.worker_process = None
        self.validator_thread = None
        self.cron_thread = None
        self.validator_pool = ThreadPoolExecutor(max_workers=2)

    def start(self):
        """
        Start the scheduler with processes for worker (fetching candidate proxies from different providers),
        and validator threads for checking whether the fetched proxies are able to use.

        """
        logging.info('Scheduler starts...')

        self.cron_thread = Thread(target=cron_schedule, args=(self,), daemon=True)
        self.worker_process = Process(target=fetch_proxies, args=(self.worker_queue, self.validator_queue))
        self.validator_thread = Thread(target=validate_ips, args=(self.validator_queue, self.validator_pool))

        self.cron_thread.daemon = True
        self.worker_process.daemon = True
        self.validator_thread.daemon = True

        self.cron_thread.start()
        self.worker_process.start()  # Python will wait for all process finished
        logging.info('worker_process started')
        self.validator_thread.start()
        logging.info('validator_thread started')

    def join(self):
        """
        Wait for worker processes and validator threads

        """
        while (self.worker_process and self.worker_process.is_alive()) or (
                self.validator_thread and self.validator_thread.is_alive()):
            try:
                self.worker_process.join()
                self.validator_thread.join()
            except (KeyboardInterrupt, SystemExit):
                break

    def feed_providers(self):
        logging.debug('feed {} providers...'.format(len(all_providers)))

        for provider in all_providers:
            self.worker_queue.put(provider)

    def stop(self):
        self.worker_queue.close()
        self.worker_process.terminate()
        # self.validator_thread.terminate() # TODO: 'terminate' the thread using a flag
        self.validator_pool.shutdown(wait=False)

def cron_schedule(scheduler, only_once=False):
    """

    :param scheduler: the Scheduler instance
    :param only_once: flag for testing
    """

    def feed():
        scheduler.feed_providers()

    def feed_from_db():

        # TODO: better query (order by attempts)
        proxies = crud.proxy.get_older_than(datetime.now() - timedelta(days=7))
        for p in proxies:
            scheduler.validator_queue.put(p)

        logging.debug('Feed {} proxies from the database for a second time validation'.format(len(proxies)))


def fetch_proxies(q: Queue, validator_queue: Queue):
    logging.debug('Fetching proxies from providers...')
    worker = Worker()

    while True:
        try:
            provider: BaseProvider = q.get()
            provider_name = provider.__class__.__name__
            logging.debug('Get a provider from the provider queue: ' + provider_name)

            for url in provider.urls():
                try:
                    pass
                except:
                    pass
        except (KeyboardInterrupt, InterruptedError, SystemExit):
            worker.stop()
            logging.info('worker_process exited.')
            break

# async def scheduler(smm_engine):
#     aioschedule.every(1).seconds.do(get_data_from_db, smm_engine)
    
#     while True:
#         await aioschedule.run_pending()
#         await asyncio.sleep(10)

# if __name__ == "__main__":
#     smm_engine = SmmEngine[sys.argv[1]]
#     asyncio.run(scheduler(smm_engine))

