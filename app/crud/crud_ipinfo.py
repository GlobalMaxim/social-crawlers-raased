from datetime import datetime
from app.crud.base import CRUDBase
from app.models.ipinfo import IPInfo
from app.schemas.ipinfo import IPInfoCreate, IPInfoUpdate
from sqlalchemy.orm import Session
from typing import List, Optional, Union, Dict, Any

class CRUDIPInfo(CRUDBase[IPInfo, IPInfoCreate, IPInfoUpdate]):
    def create(self, db: Session, *, obj_in: IPInfoCreate) -> IPInfo:
        now = datetime.now()
        db_obj = IPInfo(
            ip                  =        obj_in.ip,
            country             =        obj_in.country,
            country_iso         =        obj_in.country_iso,
            region_name         =        obj_in.region_name,
            region_code         =        obj_in.region_code,
            city                =        obj_in.city,
            latitude            =        obj_in.latitude,
            longitude           =        obj_in.longitude,
            time_zone           =        obj_in.time_zone,
            asn                 =        obj_in.asn,
            asn_org             =        obj_in.asn_org,
            hostname            =        obj_in.hostname,
            created_at          =        now,
            updated_at          =        now
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
        ip:                 str | None,
        country:            str | None,
        country_iso:        str | None,
        region_name:        str | None,
        region_code:        str | None,
        city:               str | None,
        latitude:           float | None,
        longitude:          float | None,
        time_zone:          str | None,
        asn:                str | None,
        asn_org:            str | None,
        hostname:           str | None,
        created_after:      datetime | None,
        created_before:     datetime | None,
        updated_after:      datetime | None,
        updated_before:     datetime | None,
        skip:               int = 0,
        limit:              int = 100
    ) -> List[IPInfo]:

        query = db.query(IPInfo)

        if id is not None:
            query = query.filter(IPInfo.id == id)
        if ip is not None:
            query = query.filter(IPInfo.ip == ip)
        if country is not None:
            query = query.filter(IPInfo.country == country)
        if country_iso is not None:
            query = query.filter(IPInfo.country_iso == country_iso)
        if region_name is not None:
            query = query.filter(IPInfo.region_name == region_name)
        if region_code is not None:
            query = query.filter(IPInfo.region_code == region_code)
        if city is not None:
            query = query.filter(IPInfo.city == city)
        if latitude is not None:
            query = query.filter(IPInfo.latitude == latitude)
        if longitude is not None:
            query = query.filter(IPInfo.longitude == longitude)
        if time_zone is not None:
            query = query.filter(IPInfo.time_zone == time_zone)
        if asn is not None:
            query = query.filter(IPInfo.asn == asn)
        if asn_org is not None:
            query = query.filter(IPInfo.asn_org == asn_org)
        if hostname is not None:
            query = query.filter(IPInfo.hostname == hostname)
        if created_after is not None:
            query = query.filter(IPInfo.created_at > created_after)
        if created_before is not None:
            query = query.filter(IPInfo.created_at < created_before)
        if updated_after is not None:
            query = query.filter(IPInfo.updated_at > updated_after)
        if updated_before is not None:
            query = query.filter(IPInfo.updated_at < updated_before)
        
        return query.offset(skip).limit(limit).all()

    def update(
        self, db: Session, *, db_obj: IPInfo, obj_in: Union[IPInfoUpdate, Dict[str, Any]]
    ) -> IPInfo:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        
        return super().update(db, db_obj=db_obj, obj_in=update_data)


ipinfo = CRUDIPInfo(IPInfo)
