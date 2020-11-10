#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Session backend tasks."""
from .app import app
from .utils import get_db_session
from .settings import configparser
from ..orm import Session
from ..filexfer import FileXFerEngine


@app.task
def commit_session(session_uuid):
    """Commit the session to the system."""
    xferengine = FileXFerEngine(configparser)
    # pylint: disable=invalid-name
    with get_db_session(configparser) as db:
        # pylint: disable=no-member
        session = db.query(Session).filter_by(uuid=session_uuid).first()
        xferengine.commit_session(db, session)
    print('Committed session {}'.format(session.name))
