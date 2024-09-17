from typing import Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Path, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.exceptions.crud import DuplicateEntry, PostHasNoSocialRequest, CRUDException

router = APIRouter()

@router.get("/", response_model=List[schemas.Proxy])
def read_proxy(
    db: Session = Depends(deps.get_db_local),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=0),
    current_user: models.ApiUser = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve Proxies.
    """
    proxies = crud.proxy.get_multi(
        db, skip=skip, limit=limit)
    return proxies

@router.get("/filter", response_model=List[schemas.Proxy])
def read_proxy_filter(
    db: Session = Depends(deps.get_db_local),
    # social_request_id: Optional[int] = Query(default=None, ge=1),
    id:                 int | None = Query(default=None, ge=1),
    ip:                 str | None = Query(default=None),
    port:               int | None = Query(default=None),
    username:           str | None = Query(default=None),
    password:           str | None = Query(default=None),
    is_v6:              bool | None = Query(default=None),
    is_valid:           bool | None = Query(default=None),
    is_public:          bool | None = Query(default=None),
    is_https:           bool | None = Query(default=None),
    is_socks:           bool | None = Query(default=None),
    is_anonymous:       bool | None = Query(default=None),
    is_residential:     bool | None = Query(default=None),
    is_datacenter:      bool | None = Query(default=None),
    is_mobile:          bool | None = Query(default=None),
    latency:            float | None = Query(default=None),
    stability:          float | None = Query(default=None),
    attempts:           int | None = Query(default=None),
    https_attempts:     int | None = Query(default=None),
    created_after:      datetime | None = Query(default=None),
    created_before:     datetime | None = Query(default=None),
    updated_after:      datetime | None = Query(default=None),
    updated_before:     datetime | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=0),
    current_user: models.ApiUser = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve social accounts by multiple parameters.
    """
    return crud.proxy.get_filter(
        db,
        # social_request_id=social_request_id,
        id=id,
        ip=ip,
        port=port,
        username=username,
        password=password,
        is_v6=is_v6,
        is_valid=is_valid,
        is_public=is_public,
        is_https=is_https,
        is_socks=is_socks,
        is_anonymous=is_anonymous,
        is_residential=is_residential,
        is_datacenter=is_datacenter,
        is_mobile=is_mobile,
        latency=latency,
        stability=stability,
        attempts=attempts,
        https_attempts=https_attempts,
        created_after=created_after,
        created_before=created_before,
        updated_after=updated_after,
        updated_before=updated_before,
        skip=skip,
        limit=limit,
    )

@router.post("/", response_model=schemas.Proxy)
def create_proxy(
    *,
    db: Session = Depends(deps.get_db_local),
    proxy_in: schemas.ProxyCreate,
    current_user: models.ApiUser = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create proxy.
    """
    try:
        result = crud.proxy.create(db, obj_in=proxy_in)
    except PostHasNoSocialRequest as ex:
        raise HTTPException(
            status_code=400, detail=f"{ex}"
        )
    except DuplicateEntry as ex:
        raise HTTPException(
            status_code=400, detail=f"{ex}"
        )
    except CRUDException as ex:
        raise HTTPException(
            status_code=500, detail=f"{ex}"
        )

    return result

@router.put("/proxy_id/{proxy_id}", response_model=schemas.Proxy)
def update_proxy_by_id(
    *,
    db: Session = Depends(deps.get_db_local),
    proxy_id: int = Path(ge=1),
    proxy_in: schemas.ProxyUpdate,
    current_user: models.ApiUser = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update proxy data.
    """
    # social_request_in: schemas.SocialRequestUpdate
    proxy = crud.proxy.get(db, id=proxy_id)
    if not proxy:
        raise HTTPException(
            status_code=404,
            detail="Proxy with this id does not exist in the database",
        )

    now = datetime.now()
    proxy_in.updated_at = now
    proxy_updated = crud.proxy.update(
        db,
        db_obj=proxy,
        obj_in=proxy_in
    )
    return proxy_updated