from sqlalchemy import Column, Integer, DateTime, Boolean, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class SocialLink(Base):
    __tablename__ = "social_links"

    id                   =    Column(Integer, primary_key=True, index=True)
    external_id          =    Column(Integer, nullable=False)
    social_request_id    =    Column(Integer, ForeignKey("social_requests.id"),nullable=False)
    smm_engine_id        =    Column(Integer, nullable=False)
    link                 =    Column(Text(1000), nullable=False)
    link_id              =    Column(Integer, nullable=False)
    failed               =    Column(Boolean, nullable=False, default=False)
    error_text           =    Column(String(255), nullable=True, default=None)
    created_at           =    Column(DateTime, nullable=False)
    updated_at           =    Column(DateTime, nullable=True, default=None)

    social_request = relationship("SocialRequest", back_populates="social_links")

