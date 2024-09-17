from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.mysql import INTEGER, FLOAT as Float
from datetime import datetime
from app.db.base_class import Base


UInteger = INTEGER(unsigned=True)


class IPInfo(Base):
    __tablename__ = "ipinfo"

    id                =    Column(UInteger, primary_key=True)
    ip                =    Column(String(45), unique=True, index=True)
    country           =    Column(String(64), nullable=True)
    country_iso       =    Column(String(3), nullable=True)
    region_name       =    Column(String(64), nullable=True)
    region_code       =    Column(String(3), nullable=True)
    city              =    Column(String(64), nullable=True)
    latitude          =    Column(Float, nullable=True)
    longitude         =    Column(Float, nullable=True)
    time_zone         =    Column(String(64), nullable=True)
    asn               =    Column(String(32), nullable=True)
    asn_org           =    Column(String(64), nullable=True)
    hostname          =    Column(String(255), nullable=True)
    created_at        =    Column(DateTime, nullable=False, default=datetime.now)
    updated_at        =    Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

