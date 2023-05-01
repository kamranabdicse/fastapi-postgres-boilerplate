from typing import Optional
from datetime import datetime

from pydantic import BaseModel


class RequestLogInDBBase(BaseModel):
    id: int
    created: datetime
    modified: datetime

    class Config:
        orm_mode = True


class RequestLogCreate(BaseModel):
    request: str = None
    response: str = None
    service_name: str = None
    method: str = None
    authorization: Optional[str] = None
    ip: Optional[str] = None
    trace: Optional[str] = None


class RequestLogUpdate(BaseModel):
    pass
