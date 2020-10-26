#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Session backend tasks."""
from .app import app
from .utils import get_db_session
from ..orm import Session


@app.task
def commit_session(session_uuid):
    """Commit the session to the system."""
    # pylint: disable=invalid-name
    with get_db_session() as db:
        # pylint: disable=no-member
        session = db.query(Session).filter_by(uuid=session_uuid).first()
    print('Committed session {}'.format(session.name))
