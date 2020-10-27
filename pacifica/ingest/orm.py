#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Ingest Object Relational Model Module."""
import uuid
import json
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, Text, Boolean, Float, DateTime, ForeignKey
from pacifica.auth.user_model import Base, User


def _generate_uuid():
    """Generate a random uuid."""
    return str(uuid.uuid4())


# pylint: disable=too-few-public-methods
class Session(Base):
    """Keep track of an ingest."""

    __tablename__ = 'session'
    uuid = Column(String(40), primary_key=True, default=_generate_uuid, index=True)
    name = Column(String(200), default='')
    task_uuid = Column(String(200), default='')
    task_percent = Column(Float(), default=0.0)
    user_auth = Column(Text(), default='')
    exception = Column(Text(), default='')
    jsonapi_data = Column(Text(), default='')
    processing = Column(Boolean(), default=False)
    complete = Column(Boolean(), default=False)
    user_uuid = Column(String(40), ForeignKey('user.uuid'), index=True)
    user = relationship('User')
    created = Column(DateTime(), default=datetime.utcnow)
    updated = Column(DateTime(), default=datetime.utcnow)


# pylint: disable=too-few-public-methods
class SessionEncoder(json.JSONEncoder):
    """Session json encoder."""

    def default(self, o):
        """Default method part of the API."""
        plain_keys = [
            'uuid', 'name', 'task_uuid', 'task_percent',
            'exception', 'processing', 'complete', 'user_uuid'
        ]
        if isinstance(o, Session):
            ret = {}
            for key in plain_keys:
                ret[key] = getattr(o, key)
            for key in ['user_auth', 'jsonapi_data']:
                ret[key] = json.loads(getattr(o, key))
            for key in ['created', 'updated']:
                ret[key] = getattr(o, key).isoformat()
            return ret
        return json.JSONEncoder.default(self, o)


# pylint: disable=invalid-name
def as_session(db, dct):
    """Convert a dictionary to session."""
    if 'uuid' in dct:
        session = db.query(Session).filter_by(uuid=dct['uuid']).first()
        if not session:
            return None
        for key in ['name', 'task_uuid', 'task_percent', 'exception', 'processing', 'complete', 'user_uuid']:
            if dct.get(key, False):
                setattr(session, key, dct[key])
        for key in ['user_auth', 'jsonapi_data']:
            if dct.get(key, False):
                setattr(session, key, json.dumps(dct[key]))
        for key in ['created', 'updated']:
            if dct.get(key, False):
                setattr(session, key, datetime.fromisoformat(dct[key]))
        return session
    return dct


__all__ = [
    'Session',
    'User',
    'Base'
]
