from datetime import datetime, timedelta
from typing import List
from app import crud
from app.exceptions.crud import NoSuchProfileRequest
from app.schemas.profile_request import ProfileRequestAppend, ProfileRequestCreate, ProfileRequestUpdate
from app.models.profile_request import ProfileRequest
from app.models.profile_address import ProfileAddress
from app.models.profile_phone import ProfilePhone
from app.models.profile_nickname import ProfileNickname
from app.models.profile_email import ProfileEmail
from app.models.profile_language import ProfileLanguage
from app.models.profile_messenger import ProfileMessenger
from app.models.profile_link import ProfileLink
from app.models.profile_request_link import ProfileRequestLink
from app.crud.base import CRUDBase
from sqlalchemy.orm import Session

class CRUDProfileRequest(CRUDBase[ProfileRequest, ProfileRequestCreate, ProfileRequestUpdate]):
    def create(self, db: Session, *, obj_in: ProfileRequestCreate) -> ProfileRequest:
        now = datetime.now()

        profile_request_data = obj_in.dict()
        profile_addresses_data = profile_request_data.pop('addresses')
        profile_phones_data = profile_request_data.pop('phones')
        profile_nicknames_data = profile_request_data.pop('nicknames')
        profile_emails_data = profile_request_data.pop('emails')
        profile_languages_data = profile_request_data.pop('languages')
        profile_messengers_data = profile_request_data.pop('messengers')
        profile_requests_links = profile_request_data.pop('links')
        
        db_profile_request = ProfileRequest(**profile_request_data)
        db_profile_request.created_at = now
        
        db.add(db_profile_request)
        db.commit()
        db.refresh(db_profile_request)

        profile_request_id = db_profile_request.id

        try:
            profile_links_data = {"social":[], "web":[], "youtube":[]}
            for key, values in profile_requests_links.items():
                if key == "social":
                    for link in values:
                        profile_request_link = {}
                        profile_request_link['is_associative'] = link.pop('isAssociativeSocialMedia')
                        profile_request_link['link_type'] = "SOCIAL"
                        db_link = ProfileLink(**link)
                        db_link.created_at = now
                        db.add(db_link)
                        db.commit()
                        db.refresh(db_link)
                        profile_link_id = db_link.id
                        profile_request_link['profile_request_id'] = profile_request_id
                        profile_request_link['profile_link_id'] = profile_link_id
                        db_profile_request_link = ProfileRequestLink(**profile_request_link)
                        db_profile_request_link.created_at = now
                        profile_links_data["social"].append(profile_request_link)
                        db.add(db_profile_request_link)
                if key == "youtube":
                    for link in values:
                        profile_request_link = {}
                        profile_request_link['is_associative'] = link.pop('isAssociativeYoutubeLink')
                        profile_request_link['link_type'] = "YOUTUBE"
                        db_link = ProfileLink(**link)
                        db_link.created_at = now
                        db.add(db_link)
                        db.commit()
                        db.refresh(db_link)
                        profile_link_id = db_link.id
                        profile_request_link['profile_request_id'] = profile_request_id
                        profile_request_link['profile_link_id'] = profile_link_id
                        db_profile_request_link = ProfileRequestLink(**profile_request_link)
                        db_profile_request_link.created_at = now
                        profile_links_data["youtube"].append(profile_request_link)
                        db.add(db_profile_request_link)
                if key == "web":
                    for link in values:
                        profile_request_link = {}
                        profile_request_link['is_associative'] = link.pop('isAssociativeWebLink')
                        profile_request_link['link_type'] = "WEB"
                        db_link = ProfileLink(**link)
                        db_link.created_at = now
                        db.add(db_link)
                        db.commit()
                        db.refresh(db_link)
                        profile_link_id = db_link.id
                        profile_request_link['profile_request_id'] = profile_request_id
                        profile_request_link['profile_link_id'] = profile_link_id
                        db_profile_request_link = ProfileRequestLink(**profile_request_link)
                        db_profile_request_link.created_at = now
                        profile_links_data["web"].append(profile_request_link)
                        db.add(db_profile_request_link)

            for k in profile_addresses_data:
                profile_address = {}
                profile_address['profile_request_id'] = profile_request_id
                profile_address['address'] = k
                db_profile_address = ProfileAddress(**profile_address)
                db_profile_address.created_at = now
                db.add(db_profile_address)

            for p in profile_phones_data:
                profile_phone = {}
                profile_phone['profile_request_id'] = profile_request_id
                profile_phone['number'] = p
                db_profile_phones = ProfilePhone(**profile_phone)
                db_profile_phones.created_at = now
                db.add(db_profile_phones)

            for n in profile_nicknames_data:
                profile_nickname = {}
                profile_nickname['profile_request_id'] = profile_request_id
                profile_nickname['nickname'] = n
                db_profile_nickname = ProfileNickname(**profile_nickname)
                db_profile_nickname.created_at = now
                db.add(db_profile_nickname)

            for e in profile_emails_data:
                profile_email = {}
                profile_email['profile_request_id'] = profile_request_id
                profile_email['email'] = e
                db_profile_email = ProfileEmail(**profile_email)
                db_profile_email.created_at = now
                db.add(db_profile_email)

            for le in profile_languages_data:
                le['profile_request_id'] = profile_request_id
                db_profile_language = ProfileLanguage(**le)
                db_profile_language.created_at = now
                db.add(db_profile_language)
            
            for m in profile_messengers_data:
                m['profile_request_id'] = profile_request_id
                db_profile_messenger = ProfileMessenger(**m)
                db_profile_messenger.created_at = now
                db.add(db_profile_messenger)
                
            db.commit()
        except:
            db.flush()
            self.remove(db, id=profile_request_id)
        # db_profile_request.profile_requests_links = profile_links_data
        return db_profile_request

    def get_active_profile_requests(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[ProfileRequest]:
        now = datetime.now()
        current_limit = limit
        current_skip = skip
        profile_requests_active: List[ProfileRequest] = db.query(ProfileRequest).filter(ProfileRequest.is_active == True).offset(current_skip).limit(current_limit).all()
        
        profile_request_ready_to_run: List[ProfileRequest] = []

        for profile_request in profile_requests_active:
            if profile_request.deleted_at is None:
                if profile_request.last_autocomplete_date is None:
                    profile_request_ready_to_run.append(profile_request)
                else:
                    frequency = timedelta(days=7)
                    if profile_request.last_autocomplete_date < (now - frequency):
                        profile_request_ready_to_run.append(profile_request)
        
        return profile_request_ready_to_run

    def set_deleted_at_by_external_id(self, db: Session, *, external_profile_id: int) -> ProfileRequest:
        profile_request = db.query(ProfileRequest).filter(ProfileRequest.external_id == external_profile_id).first()
        if not profile_request:
            raise NoSuchProfileRequest('Profile Request with such id does not exist')

        now = datetime.now()
        profile_request_in = {"deleted_at": now, 'is_active': False}
        profile_request_updated = crud.profile_request.update(
            db,
            db_obj=profile_request,
            obj_in=profile_request_in
        )
        return profile_request_updated
    
    def update_current_profile_request_by_external_id(self, db:Session, *, external_profile_id: int, obj_in: ProfileRequestCreate) -> ProfileRequest:
        links: List[ProfileLink] = db.query(ProfileLink).join(ProfileRequestLink).join(ProfileRequest).filter(ProfileRequest.external_id == external_profile_id).all()
        profile_request = db.query(ProfileRequest).filter(ProfileRequest.external_id == external_profile_id).first()
        # profile_request = crud.profile_request.get(db, )
        if not profile_request:
            raise NoSuchProfileRequest('Profile Request with such id does not exist')
        # else:
        #     profile_request = profile_request_query.one()
        db.delete(profile_request)
        db.commit()
        if len(links) > 0:
            for link in links:
                db.delete(link)
            db.commit()
        now = datetime.now()
        obj_in.updated_at = now
        return self.create(db=db, obj_in=obj_in)
        # print(links)

    def check_duplicates(self, db: Session, *, obj_in: ProfileRequestCreate
    ) -> list[ProfileRequest]:
        profile_request_duplicates: list[ProfileRequest] = db.query(ProfileRequest).filter(
            ProfileRequest.external_id == obj_in.external_id,
            ProfileRequest.reply_link == obj_in.reply_link
        ).all()

        return profile_request_duplicates

    def append_data_by_profile_request_id(self, db: Session, *, profile_request_id: int, obj_in: ProfileRequestAppend):
        now = datetime.now()

        db_profile_request = db.query(ProfileRequest).filter(ProfileRequest.id == profile_request_id).one()

        profile_request_data = obj_in.dict()

        if 'addresses' in profile_request_data:
            profile_addresses_data = profile_request_data.pop('addresses')
        else:
            profile_addresses_data = None
        if 'phones' in profile_request_data:
            profile_phones_data = profile_request_data.pop('phones')
        else:
            profile_phones_data = None
        if 'nicknames' in profile_request_data:
            profile_nicknames_data = profile_request_data.pop('nicknames')
        else:
            profile_nicknames_data = None
        if 'emails' in profile_request_data:
            profile_emails_data = profile_request_data.pop('emails')
        else:
            profile_emails_data = None
        if 'languages' in profile_request_data:
            profile_languages_data = profile_request_data.pop('languages')
        else:
            profile_languages_data = None
        if 'messengers' in profile_request_data:
            profile_messengers_data = profile_request_data.pop('messengers')
        else:
            profile_messengers_data = None
        if 'links' in profile_request_data:
            profile_requests_links = profile_request_data.pop('links')
        else:
            profile_requests_links = None

        for var, value in profile_request_data.items():
            setattr(db_profile_request, var, value) if value else None
        
        db_profile_request.updated_at = now
        db_profile_request.last_autocomplete_date = now
        db.add(db_profile_request)
        db.commit()
        try:
            if profile_requests_links:
                profile_links_data = {"social":[], "web":[], "youtube":[]}
                for key, values in profile_requests_links.items():
                    if key == "social":
                        for link in values:
                            profile_request_link = {}
                            profile_request_link['is_associative'] = link.pop('isAssociativeSocialMedia')
                            profile_request_link['link_type'] = "SOCIAL"
                            db_link = ProfileLink(**link)
                            db_link.created_at = now
                            db.add(db_link)
                            db.commit()
                            db.refresh(db_link)
                            profile_link_id = db_link.id
                            profile_request_link['profile_request_id'] = profile_request_id
                            profile_request_link['profile_link_id'] = profile_link_id
                            db_profile_request_link = ProfileRequestLink(**profile_request_link)
                            db_profile_request_link.created_at = now
                            profile_links_data["social"].append(profile_request_link)
                            db.add(db_profile_request_link)
                    if key == "youtube":
                        for link in values:
                            profile_request_link = {}
                            profile_request_link['is_associative'] = link.pop('isAssociativeYoutubeLink')
                            profile_request_link['link_type'] = "YOUTUBE"
                            db_link = ProfileLink(**link)
                            db_link.created_at = now
                            db.add(db_link)
                            db.commit()
                            db.refresh(db_link)
                            profile_link_id = db_link.id
                            profile_request_link['profile_request_id'] = profile_request_id
                            profile_request_link['profile_link_id'] = profile_link_id
                            db_profile_request_link = ProfileRequestLink(**profile_request_link)
                            db_profile_request_link.created_at = now
                            profile_links_data["youtube"].append(profile_request_link)
                            db.add(db_profile_request_link)
                    if key == "web":
                        for link in values:
                            profile_request_link = {}
                            profile_request_link['is_associative'] = link.pop('isAssociativeWebLink')
                            profile_request_link['link_type'] = "WEB"
                            db_link = ProfileLink(**link)
                            db_link.created_at = now
                            db.add(db_link)
                            db.commit()
                            db.refresh(db_link)
                            profile_link_id = db_link.id
                            profile_request_link['profile_request_id'] = profile_request_id
                            profile_request_link['profile_link_id'] = profile_link_id
                            db_profile_request_link = ProfileRequestLink(**profile_request_link)
                            db_profile_request_link.created_at = now
                            profile_links_data["web"].append(profile_request_link)
                            db.add(db_profile_request_link)

            if profile_addresses_data:        
                for k in profile_addresses_data:
                    profile_address = {}
                    profile_address['profile_request_id'] = profile_request_id
                    profile_address['address'] = k
                    db_profile_address = ProfileAddress(**profile_address)
                    db_profile_address.created_at = now
                    db.add(db_profile_address)
            if profile_phones_data:
                for p in profile_phones_data:
                    profile_phone = {}
                    profile_phone['profile_request_id'] = profile_request_id
                    profile_phone['number'] = p
                    db_profile_phones = ProfilePhone(**profile_phone)
                    db_profile_phones.created_at = now
                    db.add(db_profile_phones)
            if profile_nicknames_data:
                for n in profile_nicknames_data:
                    profile_nickname = {}
                    profile_nickname['profile_request_id'] = profile_request_id
                    profile_nickname['nickname'] = n
                    db_profile_nickname = ProfileNickname(**profile_nickname)
                    db_profile_nickname.created_at = now
                    db.add(db_profile_nickname)
            if profile_emails_data:
                for e in profile_emails_data:
                    profile_email = {}
                    profile_email['profile_request_id'] = profile_request_id
                    profile_email['email'] = e
                    db_profile_email = ProfileEmail(**profile_email)
                    db_profile_email.created_at = now
                    db.add(db_profile_email)
            if profile_languages_data:
                for le in profile_languages_data:
                    le['profile_request_id'] = profile_request_id
                    db_profile_language = ProfileLanguage(**le)
                    db_profile_language.created_at = now
                    db.add(db_profile_language)
            if profile_messengers_data:
                for m in profile_messengers_data:
                    m['profile_request_id'] = profile_request_id
                    db_profile_messenger = ProfileMessenger(**m)
                    db_profile_messenger.created_at = now
                    db.add(db_profile_messenger)
            
            db.commit()
        except:
            db.flush()

        return db_profile_request


profile_request = CRUDProfileRequest(ProfileRequest)