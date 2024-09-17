from typing import Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Path, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.exceptions.crud import DuplicateEntry, PostHasNoSocialRequest, CRUDException

router = APIRouter()

@router.get("/", response_model=List[schemas.IPInfo])
def read_ipinfo(
    db: Session = Depends(deps.get_db_local),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=0),
    current_user: models.ApiUser = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve IP Info.
    """
    ipinfo = crud.ipinfo.get_multi(
        db, skip=skip, limit=limit)
    return ipinfo

@router.get("/filter", response_model=List[schemas.IPInfo])
def read_ipinfo_filter(
    db: Session = Depends(deps.get_db_local),
    # social_request_id: Optional[int] = Query(default=None, ge=1),
    id:                 int | None = Query(default=None, ge=1),
    ip:                 str | None = Query(default=None),
    country:            str | None = Query(default=None),
    country_iso:        str | None = Query(default=None),
    region_name:        str | None = Query(default=None),
    region_code:        str | None = Query(default=None),
    city:               str | None = Query(default=None),
    latitude:           float | None = Query(default=None),
    longitude:          float | None = Query(default=None),
    time_zone:          str | None = Query(default=None),
    asn:                str | None = Query(default=None),
    asn_org:            str | None = Query(default=None),
    hostname:           str | None = Query(default=None),
    created_after:      datetime | None = Query(default=None),
    created_before:     datetime | None = Query(default=None),
    updated_after:      datetime | None = Query(default=None),
    updated_before:     datetime | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=0),
    current_user: models.ApiUser = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve ipinfo by multiple parameters.
    """
    return crud.ipinfo.get_filter(
        db,
        # social_request_id=social_request_id,
        id=id,
        ip=ip,
        country=country,
        country_iso=country_iso,
        region_name=region_name,
        region_code=region_code,
        city=city,
        latitude=latitude,
        longitude=longitude,
        time_zone=time_zone,
        asn=asn,
        asn_org=asn_org,
        hostname=hostname,
        created_after=created_after,
        created_before=created_before,
        updated_after=updated_after,
        updated_before=updated_before,
        skip=skip,
        limit=limit,
    )

@router.post("/", response_model=schemas.IPInfo)
def create_ipinfo(
    *,
    db: Session = Depends(deps.get_db_local),
    ipinfo_in: schemas.IPInfoCreate,
    current_user: models.ApiUser = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create IP Info.
    """
    try:
        result = crud.ipinfo.create(db, obj_in=ipinfo_in)
    except DuplicateEntry as ex:
        raise HTTPException(
            status_code=400, detail=f"{ex}"
        )
    except CRUDException as ex:
        raise HTTPException(
            status_code=500, detail=f"{ex}"
        )

    return result

@router.put("/ipinfo_id/{ipinfo_id}", response_model=schemas.IPInfo)
def update_ipinfo_by_id(
    *,
    db: Session = Depends(deps.get_db_local),
    ipinfo_id: int = Path(ge=1),
    ipinfo_in: schemas.IPInfoUpdate,
    current_user: models.ApiUser = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update IP Info data.
    """
    # social_request_in: schemas.SocialRequestUpdate
    ipinfo = crud.ipinfo.get(db, id=ipinfo_id)
    if not ipinfo:
        raise HTTPException(
            status_code=404,
            detail="Ip Info with this id does not exist in the database",
        )

    now = datetime.now()
    ipinfo_in.updated_at = now
    ipinfo_update = crud.ipinfo.update(
        db,
        db_obj=ipinfo,
        obj_in=ipinfo_in
    )
    return ipinfo_update