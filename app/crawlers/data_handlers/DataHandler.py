import logging
import requests
import json
from tenacity import after_log, retry, wait_chain, wait_fixed, RetryError
from requests import HTTPError
from fastapi.encoders import jsonable_encoder

from app.core.config import settings
from app.schemas.profile_language import ProfileLanguageBase
from app.schemas.profile_link import ProfileLink, ProfileLinkCreate
from app.schemas.profile_messenger import ProfileMessengerBase
from app.schemas.profile_request import ProfileRequest, ProfileRequestCreate
from app.schemas.profile_request_link import ProfileRequestLink
from app.schemas.profile_task import ProfileTask
from app.schemas.social_account import SocialAccount
from app.schemas.social_request import SocialRequest
from app.schemas.social_keyword import SocialKeyword
from app.schemas.social_hashtag import SocialHashtag
from app.schemas.social_link import SocialLink, SocialLinkCreate
from app.schemas.social_task import SocialTask
from app.schemas.social_parsing_post import SocialParsingPostCreate
from app.crawlers.smm_engines.smm_engines import SmmEngine
from app.logging.notify import notify


class DataHandler():

    # logging.basicConfig(level=logging.WARN, filename="app/logging/DataHandlerLog.txt")
    # logger = logging.getLogger(__name__)

    def __init__(self):
        self.api_base = f"{settings.SERVER_HOST}{settings.API_V1_STR}"
        self.api_username = settings.FIRST_SUPERUSER
        self.api_password = settings.FIRST_SUPERUSER_PASSWORD
        self.access_token = settings.ACCESS_TOKEN

    @retry(wait=wait_chain(*[wait_fixed(10) for i in range(6)] +
           [wait_fixed(30) for i in range(10)] +
           [wait_fixed(60) for i in range(60)]))
    def get_access_token(self):
        try:
            notify.info("Trying to get API access token")
            url = f'{self.api_base}/login/access-token'
            headers = {'accept': 'application/json',
                       'Content-Type': 'application/x-www-form-urlencoded'}
            data = {'username': self.api_username, 'password': self.api_password}
            response = requests.post(url, data=data, headers=headers)
            response.raise_for_status()
            if response.ok:
                notify.info('Got API access token')
            data = json.loads(response.text)
            return data['access_token']
        except HTTPError as ex:
            print(str(ex))

    def get_initial_data(self, smm_id: int):
        try:
            notify.info('Trying to get active social requests')
            # access_token = self.get_access_token()
            route = f"/social_requests/smm_id/{smm_id}"
            skip = 0
            limit = 1000
            url = f'{self.api_base}{route}?skip={skip}&limit={limit}'
            headers = {'accept': 'application/json',
                       'Authorization': f"Bearer {self.access_token}"}
            data = json.loads(requests.get(url, headers=headers).text)
            notify.info('Initial data created')
            return data
        except (Exception) as e:
            notify.error(e)
    
    def get_active_profile_requests_from_db(self):
        try:
            notify.info("Trying to get active profile requests")
            route = "/profile_requests/active_profile_requests"
            skip = 0
            limit = 1000
            url = f'{self.api_base}{route}?skip={skip}&limit={limit}'
            headers = {'accept': 'application/json',
                       'Authorization': f"Bearer {self.access_token}"}
            data = json.loads(requests.get(url, headers=headers).text)
            notify.info('Initial data for profile requests recieved')
            return data
        except (Exception) as e:
            notify.error(e)

    def get_active_account(self, smm_id: int):
        try:
            notify.info('Trying to get active account')
            # access_token = self.get_access_token()
            route = f"/social_accounts/filter?smm_id={smm_id}&is_active=true&is_twofactor=true"
            skip = 0
            limit = 1000
            url = f'{self.api_base}{route}&skip={skip}&limit={limit}'
            headers = {'accept': 'application/json',
                       'Authorization': f"Bearer {self.access_token}"}
            data = json.loads(requests.get(url, headers=headers).text)
            notify.info('Social account recieved')
            return data
        except (Exception) as e:
            notify.error(e)


    def create_task_manager(self, requests, smm_id) -> list[SocialTask]:
        """
        Create tasks from social requests
        """
        notify.info('Start creating tasks')
        try:
            tasks: list[SocialTask] = []
            # Process active social requests
            for r in requests:
                sr = SocialRequest(**r)
                """
                Process requests without social links for global crawling.
                Search entire social network by keywords and hashtags
                """
                if sr.is_global_search == True and len(sr.social_links) == 0:
                    # If request has keywords
                    if len(sr.social_keywords) > 0:
                        keyword: SocialKeyword
                        for kw in sr.social_keywords:
                            if kw.smm_engine_id == smm_id:
                                task = SocialTask(
                                    social_request_id=sr.id,
                                    external_id=sr.external_id,
                                    is_global_search=True,
                                    smm_engine_id=kw.smm_engine_id,
                                    smm_engine_name=SmmEngine(kw.smm_engine_id).name,
                                    keyword=kw.keyword,
                                    reply_link=sr.reply_link
                                )
                                tasks.append(task)
                    # If request has hashtags
                    if len(sr.social_hashtags) > 0:
                        hashtag: SocialHashtag
                        for ht in sr.social_hashtags:
                            if ht.smm_engine_id == smm_id:
                                task = SocialTask(
                                    social_request_id=sr.id,
                                    external_id=sr.external_id,
                                    is_global_search=True,
                                    smm_engine_id=ht.smm_engine_id,
                                    smm_engine_name=SmmEngine(ht.smm_engine_id).name,
                                    hashtag=ht.hashtag,
                                    reply_link=sr.reply_link
                                )
                                tasks.append(task)
                elif sr.is_global_search == False and len(sr.social_links) > 0:
                    for l in sr.social_links:
                        # If request has keywords
                        if len(sr.social_keywords) > 0:
                            keyword: SocialKeyword
                            for kw in sr.social_keywords:
                                if kw.smm_engine_id == smm_id:
                                    task = SocialTask(
                                        social_request_id=sr.id,
                                        external_id=sr.external_id,
                                        is_global_search=False,
                                        smm_engine_id=l.smm_engine_id,
                                        smm_engine_name=SmmEngine(l.smm_engine_id).name,
                                        social_link=l.link,
                                        social_link_id=l.link_id,
                                        keyword=kw.keyword,
                                        reply_link=sr.reply_link
                                    )
                                    tasks.append(task)
                        # If request has hashtags
                        if len(sr.social_hashtags) > 0:
                            hashtag: SocialHashtag
                            for ht in sr.social_hashtags:
                                if ht.smm_engine_id == smm_id:
                                    task = SocialTask(
                                        social_request_id=sr.id,
                                        external_id=sr.external_id,
                                        is_global_search=False,
                                        smm_engine_id=l.smm_engine_id,
                                        smm_engine_name=SmmEngine(l.smm_engine_id).name,
                                        social_link=l.link,
                                        social_link_id=l.link_id,
                                        hashtag=ht.hashtag,
                                        reply_link=sr.reply_link
                                    )
                                    tasks.append(task)
                        # If request has social links but no keywords and hashtags
                        if len(sr.social_keywords) == 0 and len(sr.social_hashtags) == 0:
                            task = SocialTask(
                                social_request_id=sr.id,
                                external_id=sr.external_id,
                                is_global_search=False,
                                smm_engine_id=l.smm_engine_id,
                                smm_engine_name=SmmEngine(l.smm_engine_id).name,
                                social_link=l.link,
                                social_link_id=l.link_id,
                                reply_link=sr.reply_link
                            )
                            tasks.append(task)

            notify.info(f"{len(tasks)} tasks created")
            return tasks

        except ValueError as ex:
            print(str(ex))
    
    def create_profile_task_manager(self, profile_requests: list[ProfileRequest]) -> list[ProfileTask]:
        notify.info('Start creating profile tasks')
        tasks: list[ProfileTask] = []
        for r in profile_requests:
            pr = ProfileRequest(**r)
            task = ProfileTask(
                profile_request_id = pr.id,
                country_of_origin_code = pr.country_of_origin_code,
                country_of_residence_code = pr.country_of_residence_code,
                external_id = pr.external_id,
                reply_link = pr.reply_link,
                occupation = pr.occupation,
                date_of_birth = pr.date_of_birth,
                first_name=pr.first_name,
                last_name=pr.last_name
            )
            
            if len(pr.requests_links)>0:
                for profile_request_link in pr.requests_links:
                    if profile_request_link.link_type == "SOCIAL":
                        profile_link = profile_request_link.link
                        task.social_links.append(profile_link)
                    if profile_request_link.link_type == "YOUTUBE":
                        profile_link = profile_request_link.link
                        task.youtube_links.append(profile_link)
                    if profile_request_link.link_type == "WEB":
                        profile_link = profile_request_link.link
                        task.web_links.append(profile_link)
            if len(pr.addresses) > 0:
                task.addresses = pr.addresses
            if len(pr.emails) > 0:
                task.emails = pr.emails
            if len(pr.languages) > 0:
                task.languages = pr.languages
            if len(pr.messengers) > 0:
                task.messengers = pr.messengers
            if len(pr.phones) > 0:
                task.phones = pr.phones
            if len(pr.nicknames) > 0:
                task.nicknames = pr.nicknames
            tasks.append(task)
        return tasks

    def prepare_profile_data_to_send_structure(self, profile_data: ProfileTask):
        new_profile_request = ProfileRequestCreate(
            reply_link=profile_data.reply_link,
            external_id=profile_data.external_id,
            first_name=profile_data.first_name,
            last_name = profile_data.last_name,
            date_of_birth = profile_data.date_of_birth,
            country_of_origin_code = profile_data.country_of_origin_code,
            country_of_residence_code = profile_data.country_of_residence_code,
            occupation = profile_data.occupation,
            emails=[email.email for email in profile_data.emails],
            addresses=[address.address for address in profile_data.addresses],
            messengers=[ProfileMessengerBase(account=messenger.account, messenger_name=messenger.messenger_name) for messenger in profile_data.messengers],
            phones=[phone.number for phone in profile_data.phones],
            nicknames=[nickname.nickname for nickname in profile_data.nicknames],
            languages=[ProfileLanguageBase(language_name=language.language_name, language_code=language.language_code) for language in profile_data.languages]
        )

        new_profile_request: dict = jsonable_encoder(new_profile_request)
        
        if len(profile_data.social_links) > 0:
            social_links = []
            for link in profile_data.social_links:
                social_links.append({"link": link.link, "smm_slug": link.smm_slug, "isAssociativeSocialMedia": 0})
            new_profile_request["links"]["social"] = social_links
        
        if len(profile_data.web_links) > 0:
            web_links = []
            for link in profile_data.web_links:
                web_links.append({"link": link.link, "isAssociativeWebLink": 0})
            new_profile_request["links"]["web"] = web_links
        
        if len(profile_data.youtube_links) > 0:
            youtube_links = []
            for link in profile_data.youtube_links:
                youtube_links.append({"link": link.link, "isAssociativeYoutubeLink": 0})
            new_profile_request["links"]["youtube"] = youtube_links
        
        for key, values in new_profile_request.copy().items():
            if values is None:
                del new_profile_request[key]
            elif (isinstance(values, list) or isinstance(values, dict)) and len(values) == 0:
                del new_profile_request[key]
                
        del new_profile_request["is_active"]
        return new_profile_request
        # new_profile_request.links
