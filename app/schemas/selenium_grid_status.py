from datetime import datetime
from pydantic import BaseModel, HttpUrl


class SeleniumGridNodeOSInfo(BaseModel):
    arch: str
    name: str
    version: str


class SeleniumGridNodeSlotId(BaseModel):
    hostId: str
    id: str


class SeleniumGridNodeSlotStereotype(BaseModel):
    browserName: str
    browserVersion: str
    platformName: str
    # TODO: handle colons in field names
    # "se:noVncPort": 7900,
    # "se:vncEnabled": true


class SeleniumGridNodeSlot(BaseModel):
    id: SeleniumGridNodeSlotId
    lastStarted: datetime
    session: dict | None
    stereotype: SeleniumGridNodeSlotStereotype | None


class SeleniumGridNode(BaseModel):
    id: str
    uri: HttpUrl
    maxSessions: int
    osInfo: SeleniumGridNodeOSInfo | None
    heartbeatPeriod: int
    availability: str
    version: str
    slots: list[SeleniumGridNodeSlot]


class SeleniumGridStatusValue(BaseModel):
    ready: bool
    message: str
    nodes: list[SeleniumGridNode]


class SeleniumGridStatus(BaseModel):
    value: SeleniumGridStatusValue
