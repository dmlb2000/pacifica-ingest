#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Ingest Server Main."""
import os
import shutil
import json
import peewee
import cherrypy
from .orm import read_state, update_state
from .utils import get_unique_id, create_state_response, parse_size
from .tasks import move, ingest
from .config import get_config


def error_page_default(**kwargs):
    """The default error page should always enforce json."""
    cherrypy.response.headers['Content-Type'] = 'application/json'
    return json.dumps({
        'status': kwargs['status'],
        'message': kwargs['message'],
        'traceback': kwargs['traceback'],
        'version': kwargs['version']
    })


def get_remote_user():
    """Get the remote user from cherrypy request headers."""
    return cherrypy.request.headers.get(
        get_config().get('ingest', 'auth_header'),
        get_config().get('ingest', 'default_user')
    )


def get_authed_user(func):
    """Decorator to pull out authed user."""
    def wrapper(*args, **kwargs):
        """Wrapper method."""
        return func(
            *args,
            authed_user=get_remote_user(),
            **kwargs
        )
    return wrapper


# pylint: disable=too-few-public-methods
class RestIngestState:
    """The CherryPy ingest state object."""

    exposed = True

    # Cherrypy requires these named methods.
    # pylint: disable=invalid-name
    @staticmethod
    @cherrypy.tools.json_out()
    def GET(job_id):
        """Get the ingest state for the job."""
        try:
            record = read_state(int(job_id))
        except peewee.DoesNotExist:
            raise cherrypy.HTTPError(
                '404 Not Found', 'job ID {} does not exist.'.format(job_id))
        return create_state_response(record)
    # pylint: enable=invalid-name


class RestMove:
    """Ingest the data from the service."""

    exposed = True

    # Cherrypy requires these named methods.
    # pylint: disable=invalid-name
    @staticmethod
    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    @get_authed_user
    def POST(authed_user):
        """Post the uploaded data."""
        job_id = get_unique_id(1, 'upload_job')
        update_state(job_id, 'OK', 'UPLOADING', 0)
        name = os.path.join(
            get_config().get('ingest', 'volume_path'),
            '{}.json'.format(job_id)
        )
        with open(name, 'wb') as ingest_fd:
            ingest_fd.write(json.dumps(cherrypy.request.json).encode())
        move.delay(job_id, name, authed_user)
        return create_state_response(read_state(job_id))
    # pylint: enable=invalid-name


class RestUpload:
    """Ingest the data from the service."""

    exposed = True

    # Cherrypy requires these named methods.
    # pylint: disable=invalid-name
    @staticmethod
    @cherrypy.tools.json_out()
    @get_authed_user
    def POST(authed_user):
        """Post the uploaded data."""
        job_id = get_unique_id(1, 'upload_job')
        update_state(job_id, 'OK', 'UPLOADING', 0)
        name = os.path.join(
            get_config().get('ingest', 'volume_path'),
            '{}.tar'.format(job_id)
        )
        with open(name, 'wb') as ingest_fd:
            shutil.copyfileobj(
                cherrypy.request.body, ingest_fd,
                parse_size(get_config().get('ingest', 'transfer_size'))
            )
        ingest.delay(job_id, name, authed_user)
        return create_state_response(read_state(job_id))
    # pylint: enable=invalid-name


class Root:
    """The CherryPy root object."""

    exposed = True
    get_state = RestIngestState()
    upload = RestUpload()
    move = RestMove()

    @staticmethod
    @cherrypy.tools.json_out()
    # pylint: disable=invalid-name
    def GET():
        """Return happy message about functioning service."""
        return {'message': 'Pacifica Ingest Up and Running'}
    # pylint: enable=invalid-name
# pylint: enable=too-few-public-methods
