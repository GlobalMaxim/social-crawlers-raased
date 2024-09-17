from .crud_api_user import api_user
from .crud_social_request import social_request
from .crud_social_parsing_post import social_parsing_post
from .crud_proxy import proxy
from .crud_ipinfo import ipinfo
from .crud_cookie import cookie
from .crud_social_account import social_account
from .crud_profile_request import profile_request

# For a new basic set of CRUD operations you could just do

# from .base import CRUDBase
# from app.models.item import Item
# from app.schemas.item import ItemCreate, ItemUpdate

# item = CRUDBase[Item, ItemCreate, ItemUpdate](Item)
