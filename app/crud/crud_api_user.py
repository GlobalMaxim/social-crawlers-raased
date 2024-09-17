from typing import Any, Dict, Optional, Union

from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.crud.base import CRUDBase
from app.models.api_user import ApiUser
from app.schemas.api_user import ApiUserCreate, ApiUserUpdate


class CRUDApiUser(CRUDBase[ApiUser, ApiUserCreate, ApiUserUpdate]):
    def get_by_email(self, db: Session, *, email: str) -> Optional[ApiUser]:
        return db.query(ApiUser).filter(ApiUser.email == email).first()

    def create(self, db: Session, *, obj_in: ApiUserCreate) -> ApiUser:
        db_obj = ApiUser(
            email=obj_in.email,
            hashed_password=get_password_hash(obj_in.password),
            full_name=obj_in.full_name,
            is_superuser=obj_in.is_superuser,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: ApiUser, obj_in: Union[ApiUserUpdate, Dict[str, Any]]
    ) -> ApiUser:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        if update_data["password"]:
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password
        return super().update(db, db_obj=db_obj, obj_in=update_data)

    def authenticate(self, db: Session, *, email: str, password: str) -> Optional[ApiUser]:
        user = self.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def is_active(self, user: ApiUser) -> bool:
        return user.is_active

    def is_superuser(self, user: ApiUser) -> bool:
        return user.is_superuser


api_user = CRUDApiUser(ApiUser)
