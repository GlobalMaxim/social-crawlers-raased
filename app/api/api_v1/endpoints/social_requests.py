from typing import Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Path, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps

router = APIRouter()

@router.get("/", response_model=List[schemas.SocialRequest])
def read_social_requests(
    db: Session = Depends(deps.get_db_local),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=0),
    current_user: models.ApiUser = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve social requests.
    """
    social_requests = crud.social_request.get_multi(db, skip=skip, limit=limit)
    return social_requests


@router.post("/", response_model=schemas.SocialRequest)
def create_social_request(
    *,
    db: Session = Depends(deps.get_db_local),
    social_request_in: schemas.SocialRequestCreate,
    current_user: models.ApiUser = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create social request.
    """
    # Check for duplicate entries in db
    social_request_duplicates = crud.social_request.check_duplicates(
        db, obj_in=social_request_in
    )
    if len(social_request_duplicates) > 0:
        raise HTTPException(
        status_code=400, detail=f"This social request is already in database"
    )

    return crud.social_request.create(db, obj_in=social_request_in)

@router.put("/last_run/{social_request_id}", response_model=schemas.SocialRequest)
def update_social_request_last_run(
    *,
    db: Session = Depends(deps.get_db_local),
    social_request_id: int = Path(ge=1)
) -> Any:
    """
    Update social request last run date.
    """
    # social_request_in: schemas.SocialRequestUpdate
    social_request = crud.social_request.get(db, id=social_request_id)
    if not social_request:
        raise HTTPException(
            status_code=404,
            detail="The social request with this id does not exist in the database",
        )

    now = datetime.now()
    social_request_in = {"crawling_last_run_date": now, "updated_at": now}
    social_request_updated = crud.social_request.update(
        db,
        db_obj=social_request,
        obj_in=social_request_in
    )
    return social_request_updated

@router.get("/{social_request_id}", response_model=schemas.SocialRequest)
def read_social_request_by_id(
    social_request_id: int = Path(ge=1),
    current_user: models.ApiUser = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db_local),
) -> Any:
    """
    Get a specific social request by id.
    """
    social_request = crud.social_request.get(db, id=social_request_id)
    if social_request is None:
        raise HTTPException(
        status_code=404, detail=f"The social request with this id does not exist"
    )
    return crud.social_request.get(db, id=social_request_id)

@router.get("/smm_id/{smm_id}", response_model=List[schemas.SocialRequest])
def read_social_request_by_smm_id(
    smm_id: int = Path(ge=1),
    current_user: models.ApiUser = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db_local),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=0),
) -> Any:
    """
    Get active social requests by smm id.
    """
    return crud.social_request.get_active_social_requests_by_smm_engine(db, smm_id=smm_id,skip=skip,
        limit=limit,)

