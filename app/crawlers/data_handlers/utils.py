from enum import Enum
import os
import uuid
# import logging
import requests
import urllib.request
from datetime import datetime
from http.client import HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import HttpUrl
from app.crawlers.smm_engines.smm_engines import SmmEngine
from app.schemas.profile_link import ProfileLinkCreate
from app.schemas.profile_messenger import ProfileMessengerCreate
from app.schemas.profile_request import ProfileRequestAppend
from app.schemas.profile_task import ProfileTask
from app.schemas.social_account import SocialAccount
from app.schemas.social_parsing_post import SocialParsingPostCreate
from app.core.config import settings
import pickle


api_base = f"{settings.SERVER_HOST}{settings.API_V1_STR}"


def send_post_to_api(post: SocialParsingPostCreate):
    route = "/social_parsing_posts/"
    url = f"{api_base}{route}"
    print(f'Sending post to FastAPI')
    json = jsonable_encoder(post)
    print(json)
    r = requests.post(url, json=json)
    if r.status_code != 200:
        print(r.content)
        raise HTTPException
    else:
        print(f"Post for social request {post.social_request_id} sent to FastAPI")

def prepare_reactions_to_int(amount):
    reaction_count = str(amount)
    if '.' in reaction_count and 'K' in reaction_count:
        reaction_count = int(reaction_count.replace('K', '00').replace('.',''))
    elif 'K' in reaction_count:
        reaction_count = int(reaction_count.replace('K', '000'))
    elif '.' in reaction_count and 'M' in reaction_count:
        reaction_count = int(reaction_count.replace('M', '00000').replace('.',''))
    elif 'M' in reaction_count:
        reaction_count = int(reaction_count.replace('M', '000000'))
    else:
        reaction_count = int(reaction_count.replace(',','').replace(' ', ''))
    return reaction_count

def send_post_to_reply_link(url: str, post: SocialParsingPostCreate, external_id: int):
    print(f'Sending post to: {url}')
    external_post = post
    external_post.social_request_id = external_id
    json = jsonable_encoder(post)
    print(json)
    r = requests.post(url, json=json)


def update_social_request_last_run(id: int):
    route = f"/social_requests/last_run/{id}"
    url = f"{api_base}{route}"
    print(f"Updating last run date social request ID:{id}")
    r = requests.put(url)


def save_image(links_in: list,  basedir: str, smm_engine: SmmEngine) -> list[str]:
    year, month, day = get_year_month_day()
    path = os.path.join("images", smm_engine.name, year, month, day)
    full_path = os.path.join(settings.PATH_MEDIA, basedir, path)
    os.makedirs(full_path, exist_ok=True)
    links_out = []
    if len(links_in) > 0:
        for l in links_in:
            image_filename = f'{get_guid()}.png'
            img = requests.get(l)
            with open(os.path.join(full_path, f'{image_filename}'), 'wb') as f:
                f.write(img.content)
            image_path = f'{path}/{image_filename}'
            links_out.append(image_path)
    return links_out

def cookie_manager(method: str, basedir: str, smm_engine:SmmEngine, filename: str):
    if method == "GET":
        pickle.load(open("app/crawlers/smm_engines/facebook/cookies.pkl", "rb"))
    pass

def save_byte_image(image: bytes, basedir: str, smm_engine:SmmEngine) -> str:
    year, month, day = get_year_month_day()
    path = os.path.join("images", smm_engine.name, year, month, day)
    full_path = os.path.join(settings.PATH_MEDIA, basedir, path)
    os.makedirs(full_path, exist_ok=True)
    image_filename = f'{get_guid()}.png'
    with open(os.path.join(full_path, f'{image_filename}'), 'wb') as f:
        f.write(image)
    image_path = f'{path}/{image_filename}'
    return image_path
    
def save_video(links_in: list,  basedir: str, smm_engine: SmmEngine) -> list[str]:
    year, month, day = get_year_month_day()
    path = os.path.join("videos", smm_engine.name, year, month, day)
    full_path = os.path.join(settings.PATH_MEDIA, basedir, path)
    os.makedirs(full_path, exist_ok=True)
    links_out = []
    if len(links_in) > 0:
        for l in links_in:
            video_filename = f'{get_guid()}.mp4'
            urllib.request.urlretrieve(l, os.path.join(full_path, f'{video_filename}'))
            image_path = f'{path}/{video_filename}'
            links_out.append(image_path)
    return links_out

def delete_trash_files(basedir, post: SocialParsingPostCreate):
    trash_files = []
    trash_files.append(post.video_image)
    trash_files.append(post.featured_image)
    for attachment in post.social_posts_attachments:
        trash_files.append(attachment.image_path)
        trash_files.append(attachment.video_path)
    for file_path in trash_files:
        if file_path:
            full_path = os.path.join(settings.PATH_MEDIA, basedir, file_path)
            os.remove(full_path)


def get_year_month_day():
    year = str(datetime.now().strftime("%Y"))
    month = str(datetime.now().strftime("%m"))
    day = str(datetime.now().strftime("%d"))
    return year, month, day


def get_guid() -> str:
    guid_value = str(uuid.uuid4().hex)
    return guid_value

def filter_profile_links(initial_data: ProfileTask, new_data: ProfileTask, links: list):
    now = datetime.now()
    social_links = []
    web_links = []
    youtube_links = []
    messengers = []
    smm_slugs = ['twitter', 'facebook', 'instagram', 'medium', 'reddit', 'tiktok', 'soundcloud', 'imdb', 'quora', 'tumblr', 'aparat']
    current_social_links = [i.link for i in initial_data.social_links]
    current_web_links = [i.link for i in initial_data.web_links]
    current_youtube_links = [i.link for i in initial_data.youtube_links]
    current_messengers = [i.account for i in initial_data.messengers]
    for link in links.copy():
        try:
            for smm_slug in smm_slugs:
                if smm_slug in link and link not in current_social_links:
                    social_links.append(ProfileLinkCreate(link=link, smm_slug=smm_slug, created_at=now))
                    raise
        except:
            continue
        if 'youtube' in link and link not in current_youtube_links:
            youtube_links.append(ProfileLinkCreate(link=link, created_at=now))
            continue
        elif 't.me' in link and link not in current_messengers:
            messengers.append(ProfileMessengerCreate(account=link, messenger_name='telegram', created_at=now))
            continue
        elif link not in current_web_links and link not in current_social_links:
            web_links.append(ProfileLinkCreate(link=link, created_at=now))
            continue
        
    if len(social_links) > 0:
        for social_link in social_links:
            initial_data.social_links.append(social_link)
            new_data.social_links.append(social_link) 
    if len(web_links) > 0:
        for web_link in web_links:
            initial_data.web_links.append(web_link)
            new_data.web_links.append(web_link)
    if len(youtube_links) > 0:
        for youtube_link in youtube_links:
            initial_data.youtube_links.append(youtube_link)
            new_data.youtube_links.append(youtube_link)
    if len(messengers) > 0:
        for messenger in messengers:
            initial_data.messengers.append(messenger)
            new_data.messengers.append(messenger)
    return initial_data, new_data

def send_profile_to_reply_link(profile_data):
    url = profile_data['reply_link']
    print(profile_data)
    r = requests.post(url, json=profile_data)
    if r.status_code != 200:
        print(r.content)
        # raise HTTPException
    else:
        print(f"Data for profile request sent to reply link")

def append_profile_post(profile_request_id: int, profile_data):
    route = f"/profile_requests/append_profile_request_by_id/{profile_request_id}"
    url = f"{api_base}{route}"
    print(f'Sending profile data to FastAPI')
    r = requests.put(url, json=profile_data)
    if r.status_code != 200:
        print(r.content)
        raise HTTPException
    else:
        print(f"Data for profile request {profile_request_id} sent to FastAPI")