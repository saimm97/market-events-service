import uuid

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Event(Base):
    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False, index=True)
    event_date = Column(DateTime(timezone=True), nullable=False, index=True)
    title = Column(String, nullable=False)
    details = Column(JSON, nullable=False)
    source = Column(String, nullable=False)
    provider_event_id = Column(String, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (UniqueConstraint("symbol", "event_type", "event_date", name="_symbol_event_type_date_uc"),)


class EventSyncLog(Base):
    __tablename__ = "event_sync_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String, nullable=False, unique=True, index=True)
    last_synced_at = Column(DateTime(timezone=True), nullable=False)
