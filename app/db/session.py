from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.config import settings

engine_local = create_engine(settings.SQLALCHEMY_DATABASE_URI_LOCAL, poolclass=StaticPool, echo=settings.DEBUG)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_local)

