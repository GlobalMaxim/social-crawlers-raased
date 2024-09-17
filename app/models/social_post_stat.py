from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class SocialPostStat(Base):
    __tablename__ = "social_posts_stats"

    id                        =    Column(Integer, primary_key=True, index=True)
    external_id               =    Column(Integer, nullable=True, default=None)
    social_parsing_post_id    =    Column(Integer, ForeignKey("social_parsing_posts.id"))
    likes                     =    Column(Integer, nullable=True, default=None)
    comments                  =    Column(Integer, nullable=True, default=None)
    retweets                  =    Column(Integer, nullable=True, default=None)
    subscribers               =    Column(Integer, nullable=True, default=None)
    created_at                =    Column(DateTime, nullable=False)
    updated_at                =    Column(DateTime, nullable=True, default=None)

    social_parsing_post       =    relationship("SocialParsingPost", back_populates="social_posts_stats")