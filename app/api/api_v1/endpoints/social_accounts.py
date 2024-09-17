from typing import Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Path, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.exceptions.crud import DuplicateEntry, PostHasNoSocialRequest, CRUDException

router = APIRouter()

@router.get("/", response_model=List[schemas.SocialAccount])
def read_social_account(
    db: Session = Depends(deps.get_db_local),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=0),
    current_user: models.ApiUser = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve social accounts.
    """
    social_accounts = crud.social_account.get_multi(
        db, skip=skip, limit=limit)
    return social_accounts

@router.post("/", response_model=schemas.SocialAccount)
def create_social_account(
    *,
    db: Session = Depends(deps.get_db_local),
    social_account_in: schemas.SocialAccountCreate,
    current_user: models.ApiUser = Depends(deps.get_current_active_user),
) -> Any:
    print(social_account_in)
    """
    Create social account.
    """
    try:
        result = crud.social_account.create(db, obj_in=social_account_in)
    except DuplicateEntry as ex:
        raise HTTPException(
            status_code=400, detail=f"{ex}"
        )
    except CRUDException as ex:
        raise HTTPException(
            status_code=500, detail=f"{ex}"
        )

    return result

@router.get("/filter", response_model=List[schemas.SocialAccount])
def read_social_accounts_filter(
    db: Session = Depends(deps.get_db_local),
    # social_request_id: Optional[int] = Query(default=None, ge=1),
    id:                 int | None = Query(default=None, ge=1),
    smm_id:             int | None = Query(default=None, ge=1),
    is_active:          bool | None = Query(default=None),
    is_twofactor:       bool | None = Query(default=None),
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
    return crud.social_account.get_filter(
        db,
        # social_request_id=social_request_id,
        id=id,
        smm_id=smm_id,
        is_active=is_active,
        is_twofactor=is_twofactor,
        created_after=created_after,
        created_before=created_before,
        updated_after=updated_after,
        updated_before=updated_before,
        skip=skip,
        limit=limit,
    )

@router.put("/social_account_id/{social_account_id}", response_model=schemas.SocialAccount)
def update_social_account(
    *,
    db: Session = Depends(deps.get_db_local),
    social_account_id: int = Path(ge=1),
    social_account_in: schemas.SocialAccountUpdate,
    current_user: models.ApiUser = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update social account data.
    """
    # social_request_in: schemas.SocialRequestUpdate
    social_account = crud.social_account.get(db, id=social_account_id)
    if not social_account:
        raise HTTPException(
            status_code=404,
            detail="Social account with this id does not exist in the database",
        )

    now = datetime.now()
    social_account_in.updated_at = now
    social_account_update = crud.social_account.update(
        db,
        db_obj=social_account,
        obj_in=social_account_in
    )
    return social_account_update