from typing import Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Path, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.exceptions.crud import DuplicateEntry, PostHasNoSocialRequest, CRUDException

router = APIRouter()

@router.get("/", response_model=List[schemas.Cookie])
def read_cookie(
    db: Session = Depends(deps.get_db_local),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=0),
    current_user: models.ApiUser = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve cookies.
    """
    cookies = crud.cookie.get_multi(
        db, skip=skip, limit=limit)
    return cookies

@router.post("/", response_model=schemas.Cookie)
def create_cookie(
    *,
    db: Session = Depends(deps.get_db_local),
    cookie_in: schemas.CookieCreate,
    current_user: models.ApiUser = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create cookie.
    """
    try:
        result = crud.cookie.create(db, obj_in=cookie_in)
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

@router.get("/filter", response_model=List[schemas.Cookie])
def read_cookies_filter(
    db: Session = Depends(deps.get_db_local),
    # social_request_id: Optional[int] = Query(default=None, ge=1),
    id:                 int | None = Query(default=None, ge=1),
    cookies_file:       str | None = Query(default=None),
    account_id:         int | None = Query(default=None),
    proxy_id:           int | None = Query(default=None),
    is_valid:           bool | None = Query(default=None),
    created_after:      datetime | None = Query(default=None),
    created_before:     datetime | None = Query(default=None),
    updated_after:      datetime | None = Query(default=None),
    updated_before:     datetime | None = Query(default=None),
    is_locked:          bool | None = Query(default=None),
    date_locked:        datetime | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=0),
    current_user: models.ApiUser = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve cookies by multiple parameters.
    """
    return crud.cookie.get_filter(
        db,
        # social_request_id=social_request_id,
        id=id,
        cookies_file=cookies_file,
        account_id=account_id,
        proxy_id=proxy_id,
        is_valid=is_valid,
        created_after=created_after,
        created_before=created_before,
        updated_after=updated_after,
        updated_before=updated_before,
        is_locked=is_locked,
        date_locked=date_locked,
        skip=skip,
        limit=limit,
    )

@router.get("/get_active_cookie_by_smm_id", response_model=List[schemas.Cookie])
def get_active_cookie(
    db: Session = Depends(deps.get_db_local),
    smm_id: int = Query(default=None),
    current_user: models.ApiUser = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve cookies by multiple parameters.
    """
    return crud.cookie.get_active_cookies_by_id(
        db,
        smm_id=smm_id
        # social_request_id=social_request_id,
    )

@router.post("/unlock_all_cookies/{minutes}")
def unlock_all_cookies(
    *,
    db: Session = Depends(deps.get_db_local),
    minutes: int,
    current_user: models.ApiUser = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve cookies by multiple parameters.
    """
    return crud.cookie.unlock_all_cookies(
        db,
        minutes
        # social_request_id=social_request_id,
    )

@router.put("/cookie_id/{cookie_id}", response_model=schemas.Cookie)
def update_cookie_by_id(
    *,
    db: Session = Depends(deps.get_db_local),
    cookie_id: int = Path(ge=1),
    cookie_in: schemas.CookieUpdate,
    current_user: models.ApiUser = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update cookie data.
    """
    # social_request_in: schemas.SocialRequestUpdate
    cookie = crud.cookie.get(db, id=cookie_id)
    if not cookie:
        raise HTTPException(
            status_code=404,
            detail="Cookie with this id does not exist in the database",
        )

    now = datetime.now()
    cookie_in.updated_at = now
    cookie_update = crud.cookie.update(
        db,
        db_obj=cookie,
        obj_in=cookie_in
    )
    return cookie_update