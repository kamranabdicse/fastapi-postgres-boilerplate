from sqlalchemy import Column, Integer, Text, String

from app.db.base_class import Base


class RequestLog(Base):
    id = Column(Integer, primary_key=True, index=True)

    authorization = Column(String, nullable=True)
    method = Column(String(10), nullable=True)
    service_name = Column(String(50), nullable=True)
    ip = Column(String(50), nullable=True)
    request = Column(Text, nullable=True)
    response = Column(Text, nullable=True)
    trace = Column(Text, nullable=True, default="")

    def __str__(self):
        return "%s: %s, %s" % (self.service_name, self.ip, self.created)
