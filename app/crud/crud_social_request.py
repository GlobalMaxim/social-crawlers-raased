from os import remove
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase

from app.models.social_request import SocialRequest
from app.models.social_keyword import SocialKeyword
from app.models.social_hashtag import SocialHashtag
from app.models.social_link import SocialLink
from app.schemas.social_request import SocialRequestCreate, SocialRequestUpdate

class CRUDSocialRequest(CRUDBase[SocialRequest, SocialRequestCreate, SocialRequestUpdate]):

    def get_active_social_requests_by_smm_engine(self, db: Session, *,skip: int = 0, limit: int = 100, smm_id: int
    ) -> List[SocialRequest]:

        now = datetime.now()
        active_requests_smm_id = []
        current_limit = limit
        current_skip = skip
        while True:
            requests_active: List[SocialRequest] = db.query(SocialRequest).filter(
                SocialRequest.active == True,
                SocialRequest.crawling_start_date < now,
                SocialRequest.crawling_end_date > now
            ).offset(current_skip).limit(current_limit).all()

            requests_ready_to_run: List[SocialRequest] = []

            for request in requests_active:
                if request.crawling_last_run_date is None:
                    requests_ready_to_run.append(request)
                else:
                    frequency = timedelta(seconds=request.crawling_frequency)
                    if request.crawling_last_run_date < (now - frequency):
                        requests_ready_to_run.append(request)
            
            
            for request in requests_ready_to_run:
                is_current_smm = False

                social_keyword: SocialKeyword
                for social_keyword in request.social_keywords:
                    if social_keyword.smm_engine_id == smm_id:
                        is_current_smm = True

                social_hashtag: SocialHashtag
                for social_hashtag in request.social_hashtags:
                    if social_hashtag.smm_engine_id == smm_id:
                        is_current_smm = True
                
                social_link: SocialLink
                for social_link in request.social_links:
                    if social_link.smm_engine_id == smm_id:
                        is_current_smm = True

                if is_current_smm == True:
                    active_requests_smm_id.append(request)

            if len(requests_active) == 100:
                current_skip = current_limit
            else: 
                break
        
        return active_requests_smm_id


    def check_duplicates(self, db: Session, *, obj_in: SocialRequestCreate
    ) -> list[SocialRequest]:
        social_request_duplicates: list[SocialRequest] = db.query(SocialRequest).filter(
            SocialRequest.external_id == obj_in.external_id,
            SocialRequest.reply_link == obj_in.reply_link
        ).all()

        return social_request_duplicates

    def create(self, db: Session, *, obj_in: SocialRequestCreate) -> SocialRequest:
        now = datetime.now()

        social_request_data = obj_in.dict()
        social_keywords_data = social_request_data.pop("social_keywords", None)
        social_hashtags_data = social_request_data.pop("social_hashtags", None)
        social_links_data = social_request_data.pop("social_links", None)
        
        db_social_request = SocialRequest(**social_request_data)
        db_social_request.created_at = now

        db.add(db_social_request)
        db.commit()
        db.refresh(db_social_request)

        social_request_id = db_social_request.id

        try:
            for k in social_keywords_data:
                k["social_request_id"] = social_request_id
                db_social_keyword = SocialKeyword(**k)
                db_social_keyword.created_at = now
                db.add(db_social_keyword)
        
            for h in social_hashtags_data:
                h["social_request_id"] = social_request_id
                db_social_hashtag = SocialHashtag(**h)
                db_social_hashtag.created_at = now
                db.add(db_social_hashtag)

            for l in social_links_data:
                l["social_request_id"] = social_request_id
                db_social_link = SocialLink(**l)
                db_social_link.created_at = now
                db.add(db_social_link)
            
            db.commit()
        except:
            db.flush()
            self.remove(db, id=social_request_id)
            
        return db_social_request

 
social_request = CRUDSocialRequest(SocialRequest)