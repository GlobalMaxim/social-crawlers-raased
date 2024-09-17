from datetime import datetime
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app import crud

from app.models.social_parsing_post import SocialParsingPost
from app.models.social_post_attachment import SocialPostAttachment
from app.models.social_post_reaction import SocialPostReaction
from app.models.social_post_stat import SocialPostStat
from app.models.social_post_request import SocialPostRequest
from app.models.social_request import SocialRequest
from app.schemas.social_parsing_post import SocialParsingPostUpdate, SocialParsingPostCreate
from app.exceptions.crud import DuplicateEntry, PostHasNoSocialRequest, CRUDException
from sqlalchemy.exc import DataError

class CRUDSocialParsingPost(CRUDBase[SocialParsingPost, SocialParsingPostCreate, SocialParsingPostUpdate]):

    def has_no_social_request(self, db: Session, *, social_request_id: int
                              ) -> bool:
        social_request: SocialRequest = crud.social_request.get(
            db, id=social_request_id)
        if social_request is None:
            return True
        else:
            return False

    def is_duplicate(self, db: Session, *, obj_in: SocialParsingPostCreate
                     ) -> bool:
        duplicates: list[SocialParsingPost] = db.query(SocialParsingPost).filter(
            SocialParsingPost.link_id == obj_in.link_id,
            SocialParsingPost.smm_id == obj_in.smm_id,
            SocialParsingPost.account_name == obj_in.account_name,
            SocialParsingPost.account_login == obj_in.account_login,
            SocialParsingPost.title == obj_in.title,
            SocialParsingPost.content == obj_in.content,
            SocialParsingPost.source_link == obj_in.source_link
        ).all()

        if len(duplicates) > 0:
            return True
        else:
            return False

    def create(self, db: Session, *, obj_in: SocialParsingPostCreate) -> SocialParsingPost:

        # Check if has social request
        if self.has_no_social_request(db=db, social_request_id=obj_in.social_request_id):
            raise PostHasNoSocialRequest('This SocialParsingPost has no social request')

        # Check for duplicate posts in DB
        if self.is_duplicate(db=db, obj_in=obj_in):
            raise DuplicateEntry('This social parsing post already exists in database')

        now = datetime.now()

        social_parsing_post_data = obj_in.dict()
        social_posts_attachments_data = social_parsing_post_data.pop(
            'social_posts_attachments', None)
        social_posts_reactions_data = social_parsing_post_data.pop(
            'social_posts_reactions', None)
        social_posts_stats_data = social_parsing_post_data.pop(
            'social_posts_stats', None)

        db_social_parsing_post = SocialParsingPost(**social_parsing_post_data)
        db_social_parsing_post.created_at = now

        try:
            social_parsing_post_id = None

            db.add(db_social_parsing_post)
            db.commit()
            db.refresh(db_social_parsing_post)

            social_parsing_post_id = db_social_parsing_post.id

            for a in social_posts_attachments_data:
                a['social_parsing_post_id'] = social_parsing_post_id
                db_social_post_attachment = SocialPostAttachment(**a)
                db_social_post_attachment.created_at = now
                db.add(db_social_post_attachment)

            for r in social_posts_reactions_data:
                r['social_parsing_post_id'] = social_parsing_post_id
                db_social_posts_reactions = SocialPostReaction(**r)
                db_social_posts_reactions.created_at = now
                db.add(db_social_posts_reactions)

            if social_posts_stats_data is not None:
                social_posts_stats_data['social_parsing_post_id'] = social_parsing_post_id
                db_social_posts_stats = SocialPostStat(**social_posts_stats_data)
                db_social_posts_stats.created_at = now
                db.add(db_social_posts_stats)

            db_social_posts_requests = SocialPostRequest(
                social_request_id=obj_in.social_request_id,
                social_parsing_post_id=social_parsing_post_id
            )

            db.add(db_social_posts_requests)

            db.commit()
        except Exception as ex:
            db.rollback()
            if social_parsing_post_id is not None: self.remove(db, id=social_parsing_post_id)
            db.commit()
            raise CRUDException(str(ex))

        return db_social_parsing_post


social_parsing_post = CRUDSocialParsingPost(SocialParsingPost)
