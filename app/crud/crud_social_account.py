from datetime import datetime
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app import crud
from app.exceptions.crud import DuplicateEntry, CRUDException
from sqlalchemy.exc import DataError
from typing import List, Optional, Union, Dict, Any
from app.models.social_account import SocialAccount
from app.schemas.social_account import SocialAccountUpdate, SocialAccountCreate

class CRUDSocialAccount(CRUDBase[SocialAccount, SocialAccountUpdate, SocialAccountCreate]):
    def create(self, db: Session, *, obj_in: SocialAccountCreate) -> SocialAccount:
        now = datetime.now()
        db_obj = SocialAccount(
            smm_id                      =        obj_in.smm_id,
            login                       =        obj_in.login,
            email                       =        obj_in.email,
            email_password              =        obj_in.email_password,
            password                    =        obj_in.password,
            phone                       =        obj_in.phone,
            first_name                  =        obj_in.first_name,
            last_name                   =        obj_in.last_name,
            user_agent                  =        obj_in.user_agent,
            gender                      =        obj_in.gender,
            country_iso                 =        obj_in.country_iso,
            language_iso                =        obj_in.language_iso,
            is_active                   =        obj_in.is_active,
            is_twofactor                =        obj_in.is_twofactor,
            twofactor_token             =        obj_in.twofactor_token,
            twofactor_recovery_codes    =        obj_in.twofactor_recovery_codes,
            bans_count                  =        obj_in.bans_count,
            captcha_count               =        obj_in.captcha_count,
            quality_percent             =        obj_in.quality_percent,
            created_at                  =        now,
            updated_at                  =        now
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_filter(
        self,
        db:                Session,
        *,
        id:                 int | None,
        smm_id:             int | None,
        is_active:          bool | None,
        is_twofactor:       bool | None,
        created_after:      datetime | None,
        created_before:     datetime | None,
        updated_after:      datetime | None,
        updated_before:     datetime | None,
        skip:               int = 0,
        limit:              int = 100
    ) -> List[SocialAccount]:

        query = db.query(SocialAccount)

        if id is not None:
            query = query.filter(SocialAccount.id == id)
        if smm_id is not None:
            query = query.filter(SocialAccount.smm_id == smm_id)
        if is_active is not None:
            query = query.filter(SocialAccount.is_active == is_active)
        if is_twofactor is not None:
            query = query.filter(SocialAccount.is_twofactor == is_twofactor)
        if created_after is not None:
            query = query.filter(SocialAccount.created_at > created_after)
        if created_before is not None:
            query = query.filter(SocialAccount.created_at < created_before)
        if updated_after is not None:
            query = query.filter(SocialAccount.updated_at > updated_after)
        if updated_before is not None:
            query = query.filter(SocialAccount.updated_at < updated_before)
        
        return query.offset(skip).limit(limit).all()

    def update(
        self, db: Session, *, db_obj: SocialAccount, obj_in: Union[SocialAccountUpdate, Dict[str, Any]]
    ) -> SocialAccount:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        
        return super().update(db, db_obj=db_obj, obj_in=update_data)
    
    def get_duplicates(
        self,
        db:                Session,
        *,
        smm_id:            int | None,
        login:             str | None,
        email:             str | None,
        password:          str | None,
        skip:              int = 0,
        limit:             int = 100
    ) -> List[SocialAccount]:
        query = db.query(SocialAccount).filter(
            SocialAccount.smm_id == smm_id,
            SocialAccount.login == login,
            SocialAccount.email == email,
            SocialAccount.password == password,
        ).offset(skip).limit(limit).all()
     
        return query 

social_account = CRUDSocialAccount(SocialAccount)