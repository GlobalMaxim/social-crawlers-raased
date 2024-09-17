import requests
# import logging
from selenium import webdriver
# from time import sleep
from app.crawlers.data_handlers.grid_manager import get_active_grid_httpurl


DEFAULT_TIMEOUT_SECONDS = 30

DEFAULT_USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_3) AppleWebKit/537.36 (KHTML, like Gecko) ' \
                     'Chrome/89.0.4389.90 Safari/537.36 '


class Worker:

    def __init__(self):
        """
        Initialize the worker object with HTTP client (requests)
        """
        self.test = 'hello world'
        self.requests_session = requests.Session()
        self.requests_session.headers['User-Agent'] = DEFAULT_USER_AGENT

    def stop(self):
        """Clean the session
        """
        self.requests_session.close()


class WorkerBrowser:

    def __init__(self):
        """
        Initialize the worker object with browser
        """
        self.test = 'hello world'
        self.active_grid = str(get_active_grid_httpurl("chrome"))

        self.browser = webdriver.Remote(
            command_executor=self.active_grid,
            options=webdriver.ChromeOptions()
        )

    def stop(self):
        """Clean the session
        """
        self.browser.quit()
