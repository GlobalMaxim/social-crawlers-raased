import lorem
import random
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app import crud
from app.schemas.social_request import SocialRequestCreate, SocialRequestUpdate
from app.schemas.social_keyword import SocialKeywordCreate
from app.schemas.social_hashtag import SocialHashtagCreate
from app.schemas.social_link import SocialLinkCreate
from app.tests.utils.utils import random_email, random_lower_string


def test_create_social_request(db: Session) -> None:
    pass