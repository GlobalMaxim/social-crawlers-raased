from sqlalchemy.orm import Session

from datetime import datetime, timedelta
from app.crud.base import CRUDBase
from app.models.cookie import Cookie
from app.models.social_account import SocialAccount
from app.schemas.cookie import CookieCreate, CookieUpdate
from typing import List, Optional, Union, Dict, Any


class CRUDCookie(CRUDBase[Cookie, CookieCreate, CookieUpdate]):
    def create(self, db: Session, *, obj_in: CookieCreate) -> Cookie:
        now = datetime.now()
        db_obj = Cookie(
            cookies_file            =        obj_in.cookies_file,
            account_id              =        obj_in.account_id,
            proxy_id                =        obj_in.proxy_id,
            is_valid                =        obj_in.is_valid,
            is_locked               =        obj_in.is_locked,
            date_locked             =        obj_in.date_locked,
            created_at              =        now,
            updated_at              =        now
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_filter(
        self,
        db:                 Session,
        *,
        id:                 int | None,
        cookies_file:       str | None,
        account_id:         int | None,
        proxy_id:           int | None,
        is_valid:           bool | None,
        is_locked:          bool | None,
        date_locked:        datetime | None,
        created_after:      datetime | None,
        created_before:     datetime | None,
        updated_after:      datetime | None,
        updated_before:     datetime | None,
        skip:               int = 0,
        limit:              int = 100
    ) -> List[Cookie]:

        query = db.query(Cookie)

        if id is not None:
            query = query.filter(Cookie.id == id)
        if cookies_file is not None:
            query = query.filter(Cookie.cookies_file == cookies_file)
        if account_id is not None:
            query = query.filter(Cookie.account_id == account_id)
        if proxy_id is not None:
            query = query.filter(Cookie.proxy_id == proxy_id)
        if is_valid is not None:
            query = query.filter(Cookie.is_valid == is_valid)
        if is_locked is not None:
            query = query.filter(Cookie.is_locked == is_locked)
        if created_after is not None:
            query = query.filter(Cookie.created_at > created_after)
        if created_before is not None:
            query = query.filter(Cookie.created_at < created_before)
        if updated_after is not None:
            query = query.filter(Cookie.updated_at > updated_after)
        if updated_before is not None:
            query = query.filter(Cookie.updated_at < updated_before)
        
        return query.offset(skip).limit(limit).all()

    def get_active_cookies_by_id(
        self,
        db:                 Session,
        *,
        smm_id:             int,
        skip:               int = 0,
        limit:              int = 100
    ) -> List[Cookie]:

        query = db.query(Cookie).join(SocialAccount).filter(SocialAccount.id == Cookie.account_id).filter(SocialAccount.smm_id == smm_id).filter(Cookie.is_locked == False).filter(Cookie.is_valid == True)

        return query.offset(skip).limit(limit).all()

    def unlock_all_cookies(self, db: Session, minutes: int) -> int:
        # print(datetime.now())
        query = db.query(Cookie).filter(Cookie.is_locked == True).filter(Cookie.date_locked < datetime.utcnow() - timedelta(minutes=minutes))
        affected_rows  = query.update({"is_locked": False, "date_locked": None})
        db.commit()

        return {"updated_rows_count": affected_rows} 

    def update(
        self, db: Session, *, db_obj: Cookie, obj_in: Union[CookieUpdate, Dict[str, Any]]
    ) -> Cookie:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        
        return super().update(db, db_obj=db_obj, obj_in=update_data)
    
cookie = CRUDCookie(Cookie)
