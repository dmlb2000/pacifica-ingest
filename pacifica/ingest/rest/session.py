#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Session CherryPy Rest Endpoint."""
from configparser import ConfigParser
import json
import cherrypy
from cherrypy import HTTPError
from pacifica.auth import auth_session
from ..filexfer import FileXFerEngine
from ..orm import Session, as_session, SessionEncoder
from ..tasks import commit_session


def json_handler(*args, **kwargs):
    """Handle the json output nicely."""
    # pylint: disable=protected-access
    value = cherrypy.serving.request._json_inner_handler(*args, **kwargs)
    return json.dumps(value, sort_keys=True, indent=4, cls=SessionEncoder).encode('utf-8')


class UploadSession:
    """CherryPy Upload Session."""

    exposed = True
    _cp_config = {}

    def __init__(self, configparser: ConfigParser):
        """Create the upload session."""
        super().__init__()
        self._xfer_engine = FileXFerEngine(configparser)

    @cherrypy.tools.json_out(handler=json_handler)
    @cherrypy.tools.json_in()
    @auth_session
    # pylint: disable=invalid-name
    def POST(self, uuid=None, **kwargs):
        """Update an existing or create a session."""
        if not uuid:
            session = Session()
            session.user_uuid = cherrypy.request.user.uuid
            self._xfer_engine.generate_user_auth(session)
            cherrypy.request.db.add(session)
            cherrypy.request.db.commit()
            self._xfer_engine.create_session(session)
        else:
            session = cherrypy.request.db.query(Session).filter_by(uuid=uuid).first()
        if session.user_uuid != cherrypy.request.user.uuid:
            return HTTPError(401, 'You do not own this session.')
        cherrypy.request.json['uuid'] = session.uuid
        session = as_session(cherrypy.request.db, cherrypy.request.json)
        if kwargs.get('commit', False) and not session.complete and not session.processing:
            session.processing = True
            cherrypy.request.db.add(session)
            cherrypy.request.db.commit()
            print('Trying to commit session {}'.format(session.uuid))
            session.task_uuid = commit_session.delay(session.uuid).id
        cherrypy.request.db.add(session)
        return session

    @cherrypy.tools.json_out(handler=json_handler)
    @auth_session
    # pylint: disable=invalid-name
    # pylint: disable=no-self-use
    def GET(self, uuid=None):
        """Get an existing session."""
        if not uuid:
            return [
                {
                    'session': session.uuid,
                    'uuid': session.uuid,
                    'name': session.name,
                    'processing': session.processing,
                    'complete': session.complete,
                    'task_percent': session.task_percent,
                    'exception': session.exception
                }
                for session in cherrypy.request.db.query(Session).filter_by(user_uuid=cherrypy.request.user.uuid)
            ]
        session = cherrypy.request.db.query(Session).filter_by(uuid=uuid).first()
        return session

    @auth_session
    # pylint: disable=invalid-name
    def DELETE(self, uuid):
        """Delete a given session."""
        session = cherrypy.request.db.query(Session).filter_by(uuid=uuid).first()
        self._xfer_engine.delete_session(session)
        if session.user_uuid != cherrypy.request.user.uuid:
            raise HTTPError(401, 'You do not own this session.')
        cherrypy.request.db.delete(session)
