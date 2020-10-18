#!/usr/bin/python
"""Ingest Object Relational Model Module."""
import uuid
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, Text, Boolean, Float, DateTime, ForeignKey
from pacifica.auth.user_model import Base, User

def _generate_uuid():
    return str(uuid.uuid4())

class Session(Base):
    """Keep track of an ingest."""

    __tablename__ = 'session'
    uuid = Column(String(40), primary_key=True, default=_generate_uuid, index=True)
    name = Column(String(200), default='')
    state = Column(String(200), default='')
    task_uuid = Column(String(200), default='')
    task_percent = Column(Float(), default=0.0)
    exception = Column(Text(), default='')
    jsonapi_data = Column(Text(), default='')
    complete = Column(Boolean(), default=False)
    user_uuid = Column(String(40), ForeignKey('user.uuid'), index=True)
    user = relationship("User", back_populates="sessions")
    created = Column(DateTime(), default=datetime.utcnow)
    updated = Column(DateTime(), default=datetime.utcnow)

__all__ = [
    'Session',
    'User',
    'Base'
]