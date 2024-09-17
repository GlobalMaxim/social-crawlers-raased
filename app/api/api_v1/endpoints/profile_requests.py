from typing import Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Path, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.exceptions.crud import NoSuchProfileRequest, PostHasNoSocialRequest

router = APIRouter()

@router.get("/", response_model=List[schemas.ProfileRequest])
def read_profile_requests(
    db: Session = Depends(deps.get_db_local),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=0),
    current_user: models.ApiUser = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve profile requests.
    """
    profile_requests = crud.profile_request.get_multi(db, skip=skip, limit=limit)
    print(profile_requests)
    return profile_requests

@router.get("/active_profile_requests", response_model=List[schemas.ProfileRequest])
def read_active_profile_requests(
    db: Session = Depends(deps.get_db_local),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=0),
    current_user: models.ApiUser = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve active profile requests.
    """
    profile_requests = crud.profile_request.get_active_profile_requests(db, skip=skip, limit=limit)
    return profile_requests

@router.post("/", response_model=schemas.ProfileRequest)
def create_profile_request(
    *,
    db: Session = Depends(deps.get_db_local),
    profile_request_in: schemas.ProfileRequestCreate,
    current_user: models.ApiUser = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create profile request.
    """
    # Check for duplicate entries in db
    profile_request_duplicates = crud.profile_request.check_duplicates(
        db, obj_in=profile_request_in
    )
    
    """
    If profile external_id exists in db, update profile_request
    """
    if len(profile_request_duplicates) == 1:
        external_profile_id = profile_request_in.external_id
        profile_request_update = crud.profile_request.update_current_profile_request_by_external_id(db=db, external_profile_id=external_profile_id, obj_in=profile_request_in)
        return profile_request_update

    return crud.profile_request.create(db, obj_in=profile_request_in)

@router.put("/last_run/{profile_request_id}", response_model=schemas.ProfileRequest)
def update_profile_request_last_run(
    *,
    db: Session = Depends(deps.get_db_local),
    profile_request_id: int = Path(ge=1)
) -> Any:
    """
    Update profile request last run date.
    """
    # social_request_in: schemas.SocialRequestUpdate
    profile_request = crud.profile_request.get(db, id=profile_request_id)
    if not profile_request:
        raise HTTPException(
            status_code=404,
            detail="The profile request with this id does not exist in the database",
        )

    now = datetime.now()
    profile_request_in = {"last_autocomplete_date": now, "updated_at": now}
    profile_request_updated = crud.profile_request.update(
        db,
        db_obj=profile_request,
        obj_in=profile_request_in
    )
    return profile_request_updated

@router.post("/delete_profile_request/{external_profile_id}", response_model=schemas.ProfileRequest)
def update_profile_request_last_run(
    *,
    db: Session = Depends(deps.get_db_local),
    external_profile_id: int = Path(ge=1)
) -> Any:
    """
    Set profile request deleted.
    """
    try:
        profile_request = crud.profile_request.set_deleted_at_by_external_id(db, external_profile_id=external_profile_id)
    except NoSuchProfileRequest as ex:
        raise HTTPException(
            status_code=400, detail=f"{ex}"
    )
    return profile_request


@router.put("/append_profile_request_by_id/{profile_request_id}", response_model=schemas.ProfileRequest)
def append_profile_request(
    *,
    db: Session = Depends(deps.get_db_local),
    profile_request_id: int = Path(ge=1),
    profile_request_in: schemas.ProfileRequestAppend,
    current_user: models.ApiUser = Depends(deps.get_current_active_user),
) -> Any:
    """
    Append profile request.
    """
    profile_request_append = crud.profile_request.append_data_by_profile_request_id(db=db, profile_request_id=profile_request_id, obj_in=profile_request_in)

    return profile_request_append

@router.put("/update_profile_request/{external_profile_id}", response_model=schemas.ProfileRequest)
def update_profile_request(
    *,
    db: Session = Depends(deps.get_db_local),
    external_profile_id: int = Path(ge=1),
    profile_request_in: schemas.ProfileRequestAppend,
    current_user: models.ApiUser = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update profile request.
    """
    try:
        profile_request_update = crud.profile_request.update_current_profile_request_by_external_id(db=db, external_profile_id=external_profile_id, obj_in=profile_request_in)
    except NoSuchProfileRequest as ex:
        raise HTTPException(
            status_code=400, detail=f"{ex}"
    )
        
    return profile_request_update