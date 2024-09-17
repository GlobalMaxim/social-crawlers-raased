
from datetime import datetime
import json
import requests
from decouple import config
# import tenacity
from tenacity import after_log,retry,wait_chain,wait_fixed
from tenacity import RetryError
from requests import HTTPError
import logging


class DataHandler:

    

    logging.basicConfig(level=logging.WARN, filename="app/crawlers/logging/DataHandlerLog.txt")

    logger = logging.getLogger(__name__)
    def __init__(self, scraper_name):
        self.CURRENT_URL = "127.0.0.1:8000"
        self.scraper_name = scraper_name
        # self.access_token = self.get_access_token()
        try:
            self.access_token = self.get_access_token()
        except (RetryError, HTTPError) as e:
            print(e)

    @retry(wait=wait_chain(*[wait_fixed(10) for i in range(6)] +
                           [wait_fixed(30) for i in range(10)] +
                           [wait_fixed(60) for i in range(60)]), after=after_log(logger, logging.WARN))
    def get_initial_data(self):
        try:
            print('Trying to get initial data')
            # access_token = self.get_access_token()
            smm_id = self.get_smm_engine_id_by_name()
            url = f'http://{self.CURRENT_URL}/api/v1/social_requests/smm_id/{smm_id}?skip=0&limit=100'
            headers = {'accept': 'application/json', 'Authorization': f"Bearer {self.access_token}"}
            # url = 'http://kevin.api.raased.net/api/v1/social_requests/?skip=0&limit=5'
            # headers = {'accept': 'application/json', 'Authorization': f"Bearer {self.access_token}"}
            data = json.loads(requests.get(url, headers=headers).text)
            # print(data)
            print('Initial data created')
            return data
        except (RetryError, HTTPError) as e:
            print(e)

    @retry(wait=wait_chain(*[wait_fixed(10) for i in range(6)] +
                           [wait_fixed(30) for i in range(10)] +
                           [wait_fixed(60) for i in range(60)]), after=after_log(logger, logging.WARN))
    def get_smm_engine_name_by_id(self,id):
        try:
            # access_token = self.get_access_token()
            smm_engines = {}
            url = f'http://{self.CURRENT_URL}/api/v1/smm_engines/?skip=0&limit=10'
            headers = {'accept': 'application/json', 'Authorization': f"Bearer {self.access_token}"}
            data = json.loads(requests.get(url, headers=headers).text)
            for i in data:
                smm_engines[i['id']] = i['smm_enginescol']
            return smm_engines[id]
        except Exception as ex:
            print(str(ex))

    def get_smm_engine_id_by_name(self):
        try:
            # access_token = self.get_access_token()
            url = f'http://{self.CURRENT_URL}/api/v1/smm_engines/?skip=0&limit=10'
            headers = {'accept': 'application/json', 'Authorization': f"Bearer {self.access_token}"}
            data = json.loads(requests.get(url, headers=headers).text)
            for i in data:
                for key, value in i.items():
                    if value == self.scraper_name:
                        return i['id']
        except Exception as ex:
            print(str(ex))

    @retry(wait=wait_chain(*[wait_fixed(10) for i in range(6)] +
                           [wait_fixed(30) for i in range(10)] +
                           [wait_fixed(60) for i in range(60)]), after=after_log(logger, logging.WARN))
    def get_access_token(self):
        try:
            print("trying to get access key")
            url = f'http://{self.CURRENT_URL}/api/v1/login/access-token'
            headers = {'accept': 'application/json', 'Content-Type':'application/x-www-form-urlencoded'}
            data = {'username': 'admin@example.com','password': 'admin'}
            response = requests.post(url, data = data, headers=headers)
            response.raise_for_status()
            print(response.status_code)
            data = json.loads(response.text)
            return data['access_token']
        except Exception as ex:
            print(str(ex))      

    @retry(wait=wait_chain(*[wait_fixed(10) for i in range(6)] +
                           [wait_fixed(30) for i in range(10)] +
                           [wait_fixed(60) for i in range(60)]), after=after_log(logger, logging.WARN))
    def save_social_parsing_posts(self, data:dict):
        try:
            
            url = f'http://{self.CURRENT_URL}/api/v1/social_parsing_posts/'
            headers = {'accept': 'application/json', 'Authorization': f"Bearer {self.access_token}","charset":"utf-8", 'Content-Type': 'application/json'}
            response = requests.post(url,data=data,headers=headers)
            response.raise_for_status()

        except Exception as ex:
            print(str(ex))

    def save_social_parsing_posts_full_structure(self, data, social_request_id):
        try:
            social_parsing_post = json.dumps(data[0], ensure_ascii=False).encode('utf-8')
            # print(social_parsing_post)
            social_post_stat = data[1]
            social_post_attachments = data[2]

            url = f'http://{self.CURRENT_URL}/api/v1/social_parsing_posts/'
            headers = {'accept': 'application/json', 'Authorization': f"Bearer {self.access_token}","charset":"utf-8", 'Content-Type': 'application/json'}

            response = requests.post(url,data=social_parsing_post,headers=headers)
            if response.status_code == 400:
                raise HTTPError
                
            result = json.loads(response.text)
            print('social_parsing_post saved')
            social_parsing_post_id = int(result['id'])
            # print('social_parsing_post_id: ',social_parsing_post_id)
            try:
                # print('social_request_id: ', social_request_id)
                # print('social_parsing_post_id: ', social_parsing_post_id)
                social_post_request = {'social_request_id': int(social_request_id), 'social_parsing_post_id': social_parsing_post_id}
                social_post_request = json.dumps(social_post_request, ensure_ascii=False).encode('utf-8')
                url = f'http://{self.CURRENT_URL}/api/v1/social_posts_requests/'
                headers = {'accept': 'application/json', 'Authorization': f"Bearer {self.access_token}","charset":"utf-8", 'Content-Type': 'application/json'}
                while True:
                    response = requests.post(url,data=social_post_request,headers=headers)
                    if response.status_code == 500:
                        continue
                    elif response.status_code == 200:
                        print('social_post_request Saved')
                        break
                    else:
                        print(response.status_code)
                        break
            except Exception as ex:
                print(str(ex))

            try:
                social_post_stat['social_parsing_post_id'] = social_parsing_post_id
                social_post_stat = json.dumps(social_post_stat, ensure_ascii=False).encode('utf-8')
                url = f'http://{self.CURRENT_URL}/api/v1/social_post_stats/'
                headers = {'accept': 'application/json', 'Authorization': f"Bearer {self.access_token}","charset":"utf-8", 'Content-Type': 'application/json'}
                while True:
                    response = requests.post(url,data=social_post_stat,headers=headers)
                    if response.status_code == 500:
                        continue
                    elif response.status_code == 200:
                        print('social_post_stat Saved')
                        break
                    else:
                        print(response.status_code)
                        break
            except Exception as ex:
                print(str(ex))

            for attachment in social_post_attachments:
                try:
                    attachment['social_parsing_post_id'] = social_parsing_post_id
                    social_post_attachment = json.dumps(attachment, ensure_ascii=False).encode('utf-8')
                    url = f'http://{self.CURRENT_URL}/api/v1/social_attachments/'
                    headers = {'accept': 'application/json', 'Authorization': f"Bearer {self.access_token}","charset":"utf-8", 'Content-Type': 'application/json'}
                    while True:
                        response = requests.post(url,data=social_post_attachment,headers=headers)
                        if response.status_code == 500:
                            continue
                        elif response.status_code == 200:
                            print('social_post_attachment Saved')
                            break
                        else:
                            print(response.status_code)
                            break
                except Exception as ex:
                    print(str(ex))
        except Exception as ex:
            print(str(ex))

    def create_task_manager(self):
        # print('start creating tasks')
        try:
            print('Start created tasks')
            initial_data = self.get_initial_data()
            tasks = []
            for key in initial_data:
                if key['active'] == True and key['is_global_search'] == True and len(key['social_links']) == 0:
                    if len(key['social_keywords']) > 0:
                        for keyword in key['social_keywords']:
                            task = {}
                            task['social_link'] = ""
                            task['social_link_id'] = 0
                            task['is_global_search'] = key['is_global_search']
                            task['social_request_id'] = keyword['social_request_id']
                            task['smm_engine_id'] = keyword['smm_engine_id']
                            # task['smm_engine_id'] = 1
                            # task['smm_engine_name'] = 'twitter'
                            task['smm_engine_name'] = self.get_smm_engine_name_by_id(keyword['smm_engine_id'])
                            task['hashtag'] = ""
                            task['keyword'] = keyword['keyword']['keyword']
                            tasks.append(task)
                            # print('task created')
                    if len(key['social_hashtags']) > 0:
                        for hashtag in key['social_hashtags']:
                            task = {}
                            task['social_link'] = ""
                            task['social_link_id'] = 0
                            task['is_global_search'] = key['is_global_search']
                            task['social_request_id'] = hashtag['social_request_id']
                            task['smm_engine_id'] = hashtag['smm_engine_id']
                            # task['smm_engine_id'] = 1
                            task['smm_engine_name'] = self.get_smm_engine_name_by_id(hashtag['smm_engine_id'])
                            # task['smm_engine_name'] = 'twitter'
                            task['hashtag'] = hashtag['hashtag']['hashtag']
                            task['keyword'] = ""
                            tasks.append(task)
                elif key['active'] == True and key['is_global_search'] == False and len(key['social_links']) > 0:
                    for social_link in key['social_links']:
                        link = social_link['link']
                        if len(key['social_keywords']) > 0:
                            for keyword in key['social_keywords']:
                                task = {}
                                task['social_link'] = link['link']
                                task['social_link_id'] = link['id']
                                task['is_global_search'] = key['is_global_search']
                                task['social_request_id'] = keyword['social_request_id']
                                task['smm_engine_id'] = link['smm_engine_id']
                                # task['smm_engine_id'] = 1
                                # task['smm_engine_name'] = 'twitter'
                                task['smm_engine_name'] = self.get_smm_engine_name_by_id(link['smm_engine_id'])
                                task['hashtag'] = ""
                                task['keyword'] = keyword['keyword']['keyword']
                                tasks.append(task)
                            # print('task created')
                        if len(key['social_hashtags']) > 0:
                            for hashtag in key['social_hashtags']:
                                task = {}
                                task['social_link'] = link['link']
                                task['social_link_id'] = link['id']
                                task['is_global_search'] = key['is_global_search']
                                task['social_request_id'] = hashtag['social_request_id']
                                task['smm_engine_id'] = link['smm_engine_id']
                                # task['smm_engine_id'] = 1
                                task['smm_engine_name'] = self.get_smm_engine_name_by_id(link['smm_engine_id'])
                                # task['smm_engine_name'] = 'twitter'
                                task['hashtag'] = hashtag['hashtag']['hashtag']
                                task['keyword'] = ""
                                tasks.append(task)
                        if len(key['social_hashtags']) == 0 and len(key['social_keywords']) == 0:
                            task = {}
                            task['social_link'] = link['link']
                            task['social_link_id'] = link['id']
                            task['is_global_search'] = key['is_global_search']
                            task['social_request_id'] = social_link['social_request_id']
                            task['smm_engine_id'] = link['smm_engine_id']
                            task['smm_engine_name'] = self.get_smm_engine_name_by_id(link['smm_engine_id'])
                            # task['smm_engine_name'] = 'twitter'
                            task['hashtag'] = ""
                            task['keyword'] = ""
                            tasks.append(task)
            print('tasks created')
            return tasks
        except Exception as ex:
            print(str(ex))
        
        # return tasks
    

# cur_date = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
# print(cur_date)
# DataHandler()
