#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Session backend tasks."""
import sys
import traceback
from celery import Task
from .app import app
from .utils import get_db_session
from .settings import configparser
from ..orm import Session
from ..filexfer import FileXFerEngine
from ..metaxfer import MetaXFerEngine


class SetErrorTask(Task):

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        # exc (Exception) - The exception raised by the task.
        # args (Tuple) - Original arguments for the task that failed.
        # kwargs (Dict) - Original keyword arguments for the task that failed.
        try:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            with get_db_session(configparser) as db:
                # pylint: disable=no-member
                session = db.query(Session).filter_by(task_uuid=task_id).first()
                session.complete = True
                session.exception = """
Exception: {}
Backtrace:
================
{}
                """.format(
                    str(exc),
                    ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
                )
                db.add(session)
                db.commit()
        finally:
            print('{0!r} failed: {1!r}'.format(task_id, exc))


@app.task(base=SetErrorTask)
def commit_session(session_uuid):
    """Commit the session to the system."""
    xferengine = FileXFerEngine(configparser)
    metaengine = MetaXFerEngine(configparser)
    # pylint: disable=invalid-name
    with get_db_session(configparser) as db:
        # pylint: disable=no-member
        session = db.query(Session).filter_by(uuid=session_uuid).first()
        file_meta = xferengine.commit_session(db, session)
        metaengine.upload(db, session, file_meta)
        xferengine.delete_session(session)
        session.complete = True
        db.add(session)
        db.commit()
        print('Committed session {}'.format(session.name))
