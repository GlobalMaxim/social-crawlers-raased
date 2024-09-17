from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class SocialPostReaction(Base):
    __tablename__ = "social_posts_reactions"

    id                        =    Column(Integer, primary_key=True, index=True)
    external_id               =    Column(Integer, nullable=True, default=None)
    social_parsing_post_id    =    Column(Integer, ForeignKey("social_parsing_posts.id"))
    reaction                  =    Column(String(64), nullable=False)
    count                     =    Column(Integer, nullable=False, default=0)
    created_at                =    Column(DateTime, nullable=False)
    updated_at                =    Column(DateTime, nullable=True, default=None)

    # social_parsing_posts = relationship("SocialParsingPost", back_populates="social_posts_reactions")