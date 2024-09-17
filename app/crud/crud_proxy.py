from sqlalchemy.orm import Session

from datetime import datetime
from app.crud.base import CRUDBase
from app.models.proxy import Proxy
from app.schemas.proxy import ProxyCreate, ProxyUpdate
from typing import List, Optional, Union, Dict, Any


class CRUDProxy(CRUDBase[Proxy, ProxyCreate, ProxyUpdate]):
    def create(self, db: Session, *, obj_in: ProxyCreate) -> Proxy:
        now = datetime.now()
        db_obj = Proxy(
            ip                      =        obj_in.ip,
            port                    =        obj_in.port,
            username                =        obj_in.username,
            password                =        obj_in.password,
            is_v6                   =        obj_in.is_v6,
            is_valid                =        obj_in.is_valid,
            is_public               =        obj_in.is_public,
            is_https                =        obj_in.is_https,
            is_socks                =        obj_in.is_socks,
            is_anonymous            =        obj_in.is_anonymous,
            is_residential          =        obj_in.is_residential,
            is_datacenter           =        obj_in.is_datacenter,
            is_mobile               =        obj_in.is_mobile,
            latency                 =        obj_in.latency,
            stability               =        obj_in.stability,
            attempts                =        obj_in.attempts,
            https_attempts          =        obj_in.https_attempts,
            created_at              =        now,
            updated_at              =        now
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: Proxy, obj_in: Union[ProxyUpdate, Dict[str, Any]]
    ) -> Proxy:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        
        return super().update(db, db_obj=db_obj, obj_in=update_data)
    
    def get_filter(
        self,
        db:                Session,
        *,
        id:                 int | None,
        ip:                 str | None,
        port:               int | None,
        username:           str | None,
        password:           str | None,
        is_v6:              bool | None,
        is_valid:           bool | None,
        is_public:          bool | None,
        is_https:           bool | None,
        is_socks:           bool | None,
        is_anonymous:       bool | None,
        is_residential:     bool | None,
        is_datacenter:      bool | None,
        is_mobile:          bool | None,
        latency:            float | None,
        stability:          float | None,
        attempts:           int | None,
        https_attempts:     int | None,
        created_after:      datetime | None,
        created_before:     datetime | None,
        updated_after:      datetime | None,
        updated_before:     datetime | None,
        skip:               int = 0,
        limit:              int = 100
    ) -> List[Proxy]:

        query = db.query(Proxy)

        if id is not None:
            query = query.filter(Proxy.id == id)
        if ip is not None:
            query = query.filter(Proxy.ip == ip)
        if port is not None:
            query = query.filter(Proxy.port == port)
        if username is not None:
            query = query.filter(Proxy.username == username)
        if password is not None:
            query = query.filter(Proxy.password == password)
        if is_v6 is not None:
            query = query.filter(Proxy.is_v6 == is_v6)
        if is_valid is not None:
            query = query.filter(Proxy.is_valid == is_valid)
        if is_public is not None:
            query = query.filter(Proxy.is_public == is_public)
        if is_https is not None:
            query = query.filter(Proxy.is_https == is_https)
        if is_socks is not None:
            query = query.filter(Proxy.is_socks == is_socks)
        if is_anonymous is not None:
            query = query.filter(Proxy.is_anonymous == is_anonymous)
        if is_residential is not None:
            query = query.filter(Proxy.is_residential == is_residential)
        if is_datacenter is not None:
            query = query.filter(Proxy.is_datacenter == is_datacenter)
        if is_mobile is not None:
            query = query.filter(Proxy.is_mobile == is_mobile)
        if latency is not None:
            query = query.filter(Proxy.latency == latency)
        if stability is not None:
            query = query.filter(Proxy.stability == stability)
        if attempts is not None:
            query = query.filter(Proxy.attempts == attempts)
        if https_attempts is not None:
            query = query.filter(Proxy.https_attempts == https_attempts)
        if created_after is not None:
            query = query.filter(Proxy.created_at > created_after)
        if created_before is not None:
            query = query.filter(Proxy.created_at < created_before)
        if updated_after is not None:
            query = query.filter(Proxy.updated_at > updated_after)
        if updated_before is not None:
            query = query.filter(Proxy.updated_at < updated_before)
        
        return query.offset(skip).limit(limit).all()

    def get_duplicates(
        self,
        db:                Session,
        *,
        ip:             str,
        port:           int,
        username:       str | None,
        password:       str | None,
        is_v6:          bool = False,
        is_valid:       bool = False,
        is_public:      bool = False,
        is_https:       bool = False,
        is_socks:       bool = False,
        skip:           int = 0,
        limit:          int = 100
    ) -> List[Proxy]:
        query = db.query(Proxy).filter(
            Proxy.ip == ip,
            Proxy.port == port,
            Proxy.username == username,
            Proxy.password == password,
            Proxy.is_v6 == is_v6,
            Proxy.is_valid == is_valid,
            Proxy.is_public == is_public,
            Proxy.is_https == is_https,
            Proxy.is_socks == is_socks,
        ).offset(skip).limit(limit).all()
     
        return query


proxy = CRUDProxy(Proxy)
