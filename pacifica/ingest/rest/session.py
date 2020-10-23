#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Session CherryPy Rest Endpoint."""
import cherrypy
from cherrypy import HTTPError
from pacifica.auth import auth_session
from ..orm import Session as DBSession
from ..config import get_config


def _render_session(session):
    """Render the session to json."""
    return {
        'uuid': session.uuid,
        'name': session.name,
        'state': session.state,
        'exception': session.exception,
        'jsonapi_data': session.jsonapi_data,
        'complete': session.complete,
        'created': session.created.isoformat(),
        'updated': session.updated.isoformat()
    }


class Session:

    exposed = True
    _cp_config = {}

    def __init__(self):
        super().__init__()
        self.session_path = get_config().get('ingest', 'session_path')

    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    @auth_session
    def POST(self, uuid=None, **kwargs):
        if not uuid:
            session = DBSession()
            session.user_uuid = cherrypy.request.user.uuid
            cherrypy.request.db.add(session)
            cherrypy.request.db.commit()
        else:
            session = cherrypy.request.db.query(Session).filter_by(uuid=uuid).first()
        if session.user_uuid != cherrypy.request.user.uuid:
            return HTTPError(401, 'You do not own this session.')
        for key, value in cherrypy.request.json.items():
            setattr(session, key, value)
        if kwargs.get('commit', False) and not session.complete:
            session.commit_task_uuid = commit_session.delay(
                str(cherrypy.request.db.bind.url),
                session.uuid,
                self.session_path
            ).id
        cherrypy.request.db.add(session)
        return _render_session(session)

    @cherrypy.tools.json_out()
    @auth_session
    def GET(self, uuid=None):
        if not uuid:
            return [
                {'session': session.uuid, 'name': session.name}
                for session in cherrypy.request.db.query(Session).filter_by(user_uuid=cherrypy.request.user.uuid)
            ]
        session = cherrypy.request.db.query(Session).filter_by(uuid=uuid).first()
        return _render_session(session)

    @auth_session
    def DELETE(self, uuid):
        session = cherrypy.request.db.query(Session).filter_by(uuid=uuid).first()
        if session.user_uuid != cherrypy.request.user.uuid:
            return HTTPError(401, 'You do not own this session.')
        cherrypy.request.db.delete(session)
