
from time import sleep
import requests
from imap_tools import MailBox
import re
from bs4 import BeautifulSoup
from tenacity import retry, retry_if_exception_type, wait_chain, wait_fixed
from app.logging.notify import notify

class GetLinkFromIMAP:
    def __init__(self, email, password, smm_engine):
        self.email = email
        self.password = password
        self.smm_engine = smm_engine
        self.imap_url = self.get_imap_url()

    def get_imap_url(self):
        if "outlook.com" in self.email:
            return "outlook.office365.com"

    @retry(wait=wait_chain(*[wait_fixed(10) for i in range(6)]))
    def get_message_from_email(self) -> str:
        try:
            with MailBox(self.imap_url).login(self.email, self.password) as mailbox:
                for _ in range(10):
                    for msg in mailbox.fetch(limit=3, reverse=True):
                        header = msg.subject
                        if header == "Verify your account" and self.smm_engine == "instagram":
                            code = msg.html
                            return code
                    sleep(3)
                return None   
        except Exception as ex:
            print(ex)
            raise

    def get_code_from_parsed_html(self):
        html = self.get_message_from_email()
        if html:
            parsed_html = BeautifulSoup(html, features="html.parser")
            code = parsed_html.body.find('font', attrs={'size':'6'}).text
            notify.info("Code from email recieved successfully!")
            return code
        else: 
            print('Cannot recieve link from email')
            return None
            