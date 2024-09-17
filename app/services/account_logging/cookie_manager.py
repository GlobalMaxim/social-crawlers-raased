from datetime import datetime
from http.client import HTTPException
import random
from time import sleep
from app.crawlers.data_handlers.utils import get_guid
from app.logging.notify import notify
import json
import requests
from app.core.config import settings
from app.schemas.cookie import Cookie
from app.schemas.cookie import CookieUpdate
from app.schemas.proxy import Proxy, ProxyUpdate
from app.schemas.ipinfo import IPInfoCreate, IPInfoUpdate
from app.schemas.social_account import SocialAccount
from fastapi.encoders import jsonable_encoder
from tenacity import retry, wait_chain, wait_fixed
from selenium import webdriver
import os
import pickle

@retry(wait=wait_chain(*[wait_fixed(10) for i in range(6)]))
def get_valid_cookies_by_smm_id(smm_id: int) -> Cookie | None:
    notify.info('Trying to get active cookies')
    url = f'{settings.API_BASE}/cookies/get_active_cookie_by_smm_id?smm_id={smm_id}&skip=0&limit=100'
    headers = {'accept': 'application/json',
                'Authorization': f"Bearer {settings.ACCESS_TOKEN}"}
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        print(r.content)
        raise HTTPException
    else:
        dict_cookie = json.loads(r.text)
        cookies_with_proxy = [cookie for cookie in dict_cookie if cookie["proxy_id"] != None and cookie['is_valid'] == True]
        cookies_wihout_proxy = [cookie for cookie in dict_cookie if cookie["proxy_id"] == None and cookie['is_valid'] == True ]
        if len(cookies_with_proxy) > 0:
            random_cookie = random.choice(cookies_with_proxy)
            cookie = Cookie(**random_cookie)
            notify.info(f'Active cookie with id: {cookie.id} and proxy_id: {cookie.proxy_id} recieved')
            return cookie
        elif len(cookies_wihout_proxy) > 0:
            notify.warning(f'Cookie with valid proxy was not found!')
            random_cookie = random.choice(cookies_wihout_proxy)
            cookie = Cookie(**random_cookie)

            notify.warning(f'Cookie with id: {cookie.id} recieved')
            return cookie
        else:
            notify.error('No accounts with valid Proxy! Crawling was not started!')
            return None

@retry(wait=wait_chain(*[wait_fixed(10) for i in range(6)]))
def check_account_is_valid_by_id(id: int) -> SocialAccount | None:
    url = f'{settings.API_BASE}/social_accounts/filter?id={id}&skip=0&limit=100'
    headers = {'accept': 'application/json',
                'Authorization': f"Bearer {settings.ACCESS_TOKEN}"}
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        print(r.content)
        raise HTTPException
    else:
        notify.info(f"Account data with id: {id} recieved")
        social_account = SocialAccount(**json.loads(r.text)[0])
        return social_account if social_account.is_active == True else None

@retry(wait=wait_chain(*[wait_fixed(10) for i in range(6)]))
def update_cookie_status(cookie_id: int, status: bool) -> None:
    url = f'{settings.API_BASE}/cookies/filter?id={cookie_id}&skip=0&limit=100'
    headers = {'accept': 'application/json',
                'Authorization': f"Bearer {settings.ACCESS_TOKEN}"}
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        print(r.content)
        raise HTTPException

    current_cookie = CookieUpdate(**json.loads(r.text)[0])
    current_cookie.is_valid = status
    json_cookie = jsonable_encoder(current_cookie)
    url = f'{settings.API_BASE}/cookies/cookie_id/{cookie_id}'
    headers = {'accept': 'application/json',
                'Authorization': f"Bearer {settings.ACCESS_TOKEN}"}
    r = requests.put(url, headers=headers, json=json_cookie)
    if r.status_code != 200:
        print(r.content)
        raise HTTPException
    else:
        print(f"Cookie with id: {cookie_id} updated to {status}")

@retry(wait=wait_chain(*[wait_fixed(10) for i in range(6)]))
def update_proxy_status(proxy_id: int, status: bool) -> None:
    url = f'{settings.API_BASE}/proxies/filter?id={proxy_id}&skip=0&limit=100'
    headers = {'accept': 'application/json',
                'Authorization': f"Bearer {settings.ACCESS_TOKEN}"}
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        print(r.content)
        raise HTTPException

    current_proxy = ProxyUpdate(**json.loads(r.text)[0])
    current_proxy.is_valid = status
    json_cookie = jsonable_encoder(current_proxy)
    url = f'{settings.API_BASE}/proxies/proxy_id/{proxy_id}'
    headers = {'accept': 'application/json',
                'Authorization': f"Bearer {settings.ACCESS_TOKEN}"}
    r = requests.put(url, headers=headers, json=json_cookie)
    if r.status_code != 200:
        print(r.content)
        raise HTTPException
    else:
        notify.warning(f"Proxy with id: {proxy_id} updated to {status}")

@retry(wait=wait_chain(*[wait_fixed(10) for i in range(6)]))
def get_valid_proxy() -> Proxy | None:
    notify.info('Getting new proxy')
    url = f'{settings.API_BASE}/proxies/filter?is_valid=true&skip=0&limit=100'
    headers = {'accept': 'application/json',
                'Authorization': f"Bearer {settings.ACCESS_TOKEN}"}
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        print(r.content)
        raise HTTPException
    else:
        json_proxy = json.loads(r.text) 
        if len(json_proxy) > 0:
            proxy = Proxy(**json_proxy[0])
            notify.info(f"New proxy with id: {proxy.id} recieved")
            return proxy
        else: 
            notify.warning('No available proxy')
            return None

@retry(wait=wait_chain(*[wait_fixed(10) for i in range(6)]))
def check_proxy_is_valid_by_id(proxy_id: int) -> Proxy | None:
    if proxy_id is None:
        return None
    route = f"/proxies/filter?id={proxy_id}"
    skip = 0
    limit = 1000
    url = f'{settings.API_BASE}{route}&skip={skip}&limit={limit}'
    headers = {'accept': 'application/json',
                'Authorization': f"Bearer {settings.ACCESS_TOKEN}"}
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        print(r.content)
        raise HTTPException
    else:
        proxy = Proxy(**json.loads(r.text)[0])
        return proxy if proxy.is_valid == True else None

@retry(wait=wait_chain(*[wait_fixed(10) for i in range(6)]))
def update_cookie_by_id(cookie_id: int, new_cookie: Cookie) -> None:
    route = f"/cookies/cookie_id/{cookie_id}"
    url = f'{settings.API_BASE}{route}'
    headers = {'accept': 'application/json',
                'Authorization': f"Bearer {settings.ACCESS_TOKEN}"}

    json_cookie = jsonable_encoder(new_cookie)
    r = requests.put(url, headers=headers, json=json_cookie)
    if r.status_code != 200:
        print(r.content)
        raise HTTPException

@retry(wait=wait_chain(*[wait_fixed(10) for i in range(6)]))
def check_proxy_on_ipinfo_by_proxy_id(proxy_id: int) -> bool:
    # Get proxy by proxy_id from proxies table
    notify.info('Start checking proxy on ipinfo')
    route = f"/proxies/filter?id={proxy_id}"
    skip = 0
    limit = 1000
    url = f'{settings.API_BASE}{route}&skip={skip}&limit={limit}'
    headers = {'accept': 'application/json',
                'Authorization': f"Bearer {settings.ACCESS_TOKEN}"}
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        print(r.content)
        raise HTTPException

    # Getting info from website by proxy.ip 
    proxy = Proxy(**json.loads(r.text)[0])
    
    if proxy.username is not None:
        full_proxy = f"http://{proxy.username}:{proxy.password}@{proxy.ip.exploded}:{proxy.port}"
    else:
        full_proxy = f"http://{proxy.ip.exploded}:{proxy.port}"
    proxies = { 
        "http"  : full_proxy, 
        "https" : full_proxy
        }
    r = requests.get('https://ipinfo.dunaisky.com/json', proxies=proxies)
    if r.status_code != 200:
        # Изменяем статус прокси на False
        update_proxy_status(proxy_id, False)
        print(r.content)
        raise HTTPException
    old_ipinfo = json.loads(r.content)

    # Getting ip data from ipinfo table
    route = f"/ipinfo/filter?ip={old_ipinfo['ip']}"
    url = f'{settings.API_BASE}{route}&skip={skip}&limit={limit}'
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        print(r.content)
        raise HTTPException
    new_ipinfo_list = json.loads(r.text)

    # Check availability of such ip ipinfo table
    if len(new_ipinfo_list) == 0:
        # Если ip в базе отсутствует, добавляем его
        old_ipinfo['created_at'] = datetime.now()
        old_ipinfo_schema = IPInfoCreate.parse_obj(old_ipinfo)
        old_ipinfo_json = jsonable_encoder(old_ipinfo_schema)
        route = f"/ipinfo/"
        url = f'{settings.API_BASE}{route}'
        r = requests.post(url, json=old_ipinfo_json)
        if r.status_code != 200:
            print(r.content)
            raise HTTPException
    else:
        # If we have ip in our databes take it and compare with ip from website
        new_ipinfo = new_ipinfo_list[0]
        old_ipinfo['created_at'] = new_ipinfo['created_at'] = datetime.now()
        old_ipinfo_schema = IPInfoCreate.parse_obj(old_ipinfo)
        new_ipinfo_schema = IPInfoCreate.parse_obj(new_ipinfo)
        # If they are diffrernt, compare them and update ip in our database
        if old_ipinfo_schema != new_ipinfo_schema:
            new_ipinfo_json_to_update = old_ipinfo_schema.dict()
            new_ipinfo_json_to_update['updated_at'] = datetime.now()
            new_ipinfo_json_to_update = jsonable_encoder(IPInfoUpdate.parse_obj(new_ipinfo_json_to_update))
            route = f"/ipinfo/ipinfo_id/{new_ipinfo['id']}"
            url = f'{settings.API_BASE}{route}'
            r = requests.put(url, json=new_ipinfo_json_to_update)
            if r.status_code != 200:
                print(r.content)
                raise HTTPException
            notify.warning('IPInfo in database updated')
        else:
            notify.info('IPInfo in database not updated')

@retry(wait=wait_chain(*[wait_fixed(10) for i in range(6)]))
def change_lock_cookie_status(cookie_id: int, status: bool):
    url = f'{settings.API_BASE}/cookies/filter?id={cookie_id}&skip=0&limit=100'
    headers = {'accept': 'application/json',
                'Authorization': f"Bearer {settings.ACCESS_TOKEN}"}
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        print(r.content)
        raise HTTPException

    current_cookie = CookieUpdate(**json.loads(r.text)[0])
    current_cookie.is_locked = status
    if status:
        current_cookie.date_locked = datetime.utcnow()
    else:
        current_cookie.date_locked = None
    update_cookie_by_id(cookie_id, current_cookie)
    if status:
        current_cookie.date_locked = datetime.utcnow()
        notify.info(f'Cookie with id: {cookie_id} was locked')
    else:
        current_cookie.date_locked = None
        notify.info(f'Cookie with id: {cookie_id} was unlocked')

def get_cookie_file(cookie_model: Cookie, basedir: str):
    file_path = cookie_model.cookies_file
    full_path = os.path.join(settings.PATH_MEDIA, basedir, file_path)
    try:
        cookies = pickle.load(
            open(full_path, "rb"))
    except:
        raise FileNotFoundError
    return cookies

def save_cookies_to_file(driver: webdriver.Remote, cookie_model: Cookie, smm_engine_name: str, basedir: str, is_cookie_valid=True):
    current_cookies = driver.get_cookies()
    file_path = cookie_model.cookies_file
    full_path = os.path.join(settings.PATH_MEDIA, basedir, file_path)
    if is_cookie_valid:
        pickle.dump(current_cookies, open(
                full_path, "wb"))
    else:
        try:
            os.remove(full_path)
        except:
            pass
        cookie_new_name = f"{cookie_model.id}_{get_guid()}.pkl"
        path = os.path.join("cookies", smm_engine_name)
        full_path = os.path.join(settings.PATH_MEDIA, basedir, path)
        os.makedirs(full_path, exist_ok=True)
        pickle.dump(current_cookies, open(
                f"{full_path}/{cookie_new_name}", "wb"))
        cookie_path = f"{path}/{cookie_new_name}"
        cookie_model.cookies_file = cookie_path

        json_cookie = jsonable_encoder(cookie_model)
        url = f'{settings.API_BASE}/cookies/cookie_id/{cookie_model.id}'
        headers = {'accept': 'application/json',
                    'Authorization': f"Bearer {settings.ACCESS_TOKEN}"}
        r = requests.put(url, headers=headers, json=json_cookie)
        if r.status_code != 200:
            print(r.content)
            raise HTTPException
        notify.info(f'Cookie with id: {cookie_model.id} updated!')



@retry(wait=wait_chain(*[wait_fixed(10) for i in range(6)]))
def get_full_account_info(smm_id: int) -> tuple[SocialAccount, Cookie, Proxy]:
    active_cookie = get_valid_cookies_by_smm_id(smm_id)
    if active_cookie:
        social_account = check_account_is_valid_by_id(active_cookie.account_id)
        if not social_account: 
            update_cookie_status(active_cookie.id, False)
            get_full_account_info()
        else:
            proxy = check_proxy_is_valid_by_id(active_cookie.proxy_id)
            if not proxy:
                notify.warning(f'Proxy for cookie.id: {active_cookie.id} is invalid!')
                new_proxy = get_valid_proxy()
                if new_proxy is not None:
                    active_cookie.proxy_id = new_proxy.id
                else:
                    active_cookie.proxy_id = None
                    proxy = None
                update_cookie_by_id(active_cookie.id, active_cookie)
                notify.warning(f'Proxy for cookie_id: {active_cookie.id} updated to proxy_id: {active_cookie.proxy_id}')
                # Write to log
            else:
                try:
                    check_proxy_on_ipinfo_by_proxy_id(proxy.id)
                except HTTPException:
                    update_proxy_status(proxy.id, False)
                    get_full_account_info()

            change_lock_cookie_status(active_cookie.id, True)
            return social_account, active_cookie, proxy
    else:
        notify.error('No cookies available!')        
        raise Exception

def unlock_all_cookies(minutes: int):
    route = f"/cookies/unlock_all_cookies/{minutes}"
    url = f'{settings.API_BASE}{route}'
    r = json.loads(requests.post(url).text)
    if r['updated_rows_count'] > 0:
        print(r)
    if r.status_code != 200:
        print(r)
    #     raise HTTPException
    