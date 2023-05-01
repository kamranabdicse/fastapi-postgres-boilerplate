from app.crud.base import CRUDBase
from app.schemas.request_log import RequestLogCreate, RequestLogUpdate
from app.models.request_log import RequestLog


class CRUDRequestLog(CRUDBase[RequestLog, RequestLogCreate, RequestLogUpdate]):
    pass


request_log = CRUDRequestLog(RequestLog)
