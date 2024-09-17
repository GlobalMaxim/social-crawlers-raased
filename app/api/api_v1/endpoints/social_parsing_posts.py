from typing import Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Path, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.exceptions.crud import DuplicateEntry, PostHasNoSocialRequest, CRUDException

router = APIRouter()


@router.get("/", response_model=List[schemas.SocialParsingPost])
def read_social_parsing_post(
    db: Session = Depends(deps.get_db_local),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=0),
    current_user: models.ApiUser = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve social parsing posts.
    """
    social_parsing_posts = crud.social_parsing_post.get_multi(
        db, skip=skip, limit=limit)
    return social_parsing_posts


@router.post("/", response_model=schemas.SocialParsingPost)
def create_social_parsing_post(
    *,
    db: Session = Depends(deps.get_db_local),
    social_parsing_post_in: schemas.SocialParsingPostCreate,
    # current_user: models.ApiUser = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create social parsing post.
    """
    try:
        result = crud.social_parsing_post.create(db, obj_in=social_parsing_post_in)
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
