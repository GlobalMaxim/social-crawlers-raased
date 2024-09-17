from typing import Any, List

from fastapi import APIRouter, Body, Path, Query, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic.networks import EmailStr
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core.config import settings
from app.utils import send_new_account_email

router = APIRouter()


@router.get("/", response_model=List[schemas.ApiUser])
def read_users(
    db: Session = Depends(deps.get_db_local),
    skip: int = 0,
    limit: int = 100,
    current_user: models.ApiUser = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Retrieve users.
    """
    users = crud.api_user.get_multi(db, skip=skip, limit=limit)
    return users


@router.post("/", response_model=schemas.ApiUser)
def create_user(
    *,
    db: Session = Depends(deps.get_db_local),
    user_in: schemas.ApiUserCreate,
    current_user: models.ApiUser = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Create new user.
    """
    user = crud.api_user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    user = crud.api_user.create(db, obj_in=user_in)
    if settings.EMAILS_ENABLED and user_in.email:
        send_new_account_email(
            email_to=user_in.email, username=user_in.email, password=user_in.password
        )
    return user


@router.put("/me", response_model=schemas.ApiUser)
def update_user_me(
    *,
    db: Session = Depends(deps.get_db_local),
    password: str = Body(None),
    full_name: str = Body(None),
    email: EmailStr = Body(None),
    current_user: models.ApiUser = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update own user.
    """
    current_user_data = jsonable_encoder(current_user)
    user_in = schemas.ApiUserUpdate(**current_user_data)
    if password is not None:
        user_in.password = password
    if full_name is not None:
        user_in.full_name = full_name
    if email is not None:
        user_in.email = email
    user = crud.api_user.update(db, db_obj=current_user, obj_in=user_in)
    return user


@router.get("/me", response_model=schemas.ApiUser)
def read_user_me(
    db: Session = Depends(deps.get_db_local),
    current_user: models.ApiUser = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get current user.
    """
    return current_user


@router.get("/{user_id}", response_model=schemas.ApiUser)
def read_user_by_id(
    user_id: int = Path(ge=1),
    current_user: models.ApiUser = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db_local),
) -> Any:
    """
    Get a specific user by id.
    """
    user = crud.api_user.get(db, id=user_id)
    if user is None:
        raise HTTPException(
            status_code=404, detail=f"The user with this id does not exist"
        )
    if user == current_user:
        return user
    if not crud.api_user.is_superuser(current_user):
        raise HTTPException(
            status_code=400, detail="The user does not have enough privileges"
        )
    return user


@router.put("/", response_model=schemas.ApiUser)
def update_user(
    *,
    db: Session = Depends(deps.get_db_local),
    email: EmailStr = Query(),
    password: str = Body(None),
    full_name: str = Body(None),
    is_superuser: bool = Body(False),
    is_active: bool = Body(None),
    current_user: models.ApiUser = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Update a user.
    """
    user_in = schemas.ApiUserUpdate(
        password=password,
        full_name=full_name,
        email=email,
        is_superuser=is_superuser,
        is_active=is_active
    )
    user = crud.api_user.get_by_email(db, email=email)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this email does not exist in the system",
        )
    user_updated = crud.api_user.update(db, db_obj=user, obj_in=user_in)
    return user_updated
 