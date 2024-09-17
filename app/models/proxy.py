from sqlalchemy import Column, DateTime, Boolean, String
from sqlalchemy.dialects.mysql import INTEGER, SMALLINT, FLOAT
from datetime import datetime
from app.db.base_class import Base


UInteger = INTEGER(unsigned=True)
USmallInt = SMALLINT(unsigned=True)
UFloat = FLOAT(unsigned=True)


class Proxy(Base):
    __tablename__ = "proxies"

    id                =    Column(UInteger, primary_key=True)
    ip                =    Column(String(45), nullable=False, index=True)
    port              =    Column(USmallInt, nullable=False, index=True)
    username          =    Column(String(64), nullable=True)
    password          =    Column(String(64), nullable=True)
    is_v6             =    Column(Boolean, nullable=False, default=False)
    is_valid          =    Column(Boolean, nullable=False, default=False)
    is_public         =    Column(Boolean, nullable=False, default=False)
    is_https          =    Column(Boolean, nullable=False, default=False)
    is_socks          =    Column(Boolean, nullable=False, default=False)
    is_anonymous      =    Column(Boolean, nullable=False, default=False)
    is_residential    =    Column(Boolean, nullable=False, default=False)
    is_datacenter     =    Column(Boolean, nullable=False, default=False)
    is_mobile         =    Column(Boolean, nullable=False, default=False)
    latency           =    Column(UFloat, nullable=False, default=0.0)
    stability         =    Column(UFloat, nullable=False, default=0.0)
    attempts          =    Column(UInteger, nullable=False, default=0)
    https_attempts    =    Column(UInteger, nullable=False, default=0)
    created_at        =    Column(DateTime, nullable=False, default=datetime.now)
    updated_at        =    Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

