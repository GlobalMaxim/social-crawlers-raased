from sqlalchemy import Column, Integer, DateTime, Boolean, String, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class SocialKeyword(Base):
    __tablename__ = "social_keywords"

    id                   =    Column(Integer, primary_key=True, index=True)
    external_id          =    Column(Integer, nullable=False)
    social_request_id    =    Column(Integer, ForeignKey("social_requests.id"),nullable=False)
    smm_engine_id        =    Column(Integer, nullable=False)
    keyword              =    Column(String(255), nullable=False)
    operator             =    Column(String(7), nullable=False)
    failed               =    Column(Boolean, nullable=False, default=False)
    error_text           =    Column(String(255), nullable=True, default=None)
    created_at           =    Column(DateTime, nullable=False)
    updated_at           =    Column(DateTime, nullable=True, default=None)

    social_request = relationship("SocialRequest", back_populates="social_keywords")

