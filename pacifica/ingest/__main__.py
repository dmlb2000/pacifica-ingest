#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Ingest module."""
from configparser import ConfigParser
import os
import json
from sys import argv as sys_argv
import cherrypy
from sqlalchemy.engine import create_engine
from pacifica.auth import error_page_default, quickstart, create_configparser, create_argparser
from .rest import UploadSession
from .tasks import get_db_session
from .orm import User, Base, Session, SessionEncoder
from .config import ingest_config


def _mount_config(configparser: ConfigParser):
    common_config = {
        '/': {
            'error_page.default': error_page_default,
            'request.dispatch': cherrypy.dispatch.MethodDispatcher()
        }
    }
    cherrypy.tree.mount(UploadSession(configparser), '/session', config=common_config)
    ingest_config(configparser)


def main(argv=None):
    """Main method to start the httpd server."""
    quickstart(argv, 'Run the ingest server.', User, 'pacifica.ingest.orm.User',
               os.path.dirname(__file__), _mount_config)


def cmd(argv=None):
    """Command line admin tool for managing ingest."""
    parser = create_argparser(argv, 'Admin command line tool.')
    parser.set_defaults(func=lambda x: parser.print_help())
    subparsers = parser.add_subparsers(help='sub-command help')
    setup_job_subparser(subparsers)
    setup_db_subparser(subparsers)
    args = parser.parse_args(argv)
    configparser = create_configparser(args, ingest_config)
    return args.func(args, configparser)


def setup_job_subparser(subparsers):
    """Add the job subparser."""
    job_parser = subparsers.add_parser(
        'job', help='job help', description='manage jobs')
    job_parser.add_argument(
        'job_uuids', type=str, nargs='+',
        help='get jobs from passed options.'
    )
    job_parser.set_defaults(func=job_output)


def setup_db_subparser(subparsers):
    """Setup the dbsync subparser."""
    db_parser = subparsers.add_parser(
        'dbsync',
        description='Update or Create the Database.'
    )
    db_parser.set_defaults(func=dbsync)


def job_output(args, configparser):
    """Dump the jobs requested from the command line."""
    sessions = []
    # pylint: disable=invalid-name
    with get_db_session(configparser) as db:
        for job_uuid in args.job_uuids:
            # pylint: disable=no-member
            sessions.append(db.query(Session).filter_by(uuid=job_uuid).first())
    print(json.dumps(sessions, sort_keys=True, indent=4, cls=SessionEncoder))
    return 0


def dbsync(_args, configparser):
    """Create/Update the database schema to current code."""
    engine = create_engine(configparser.get('database', 'db_url'))
    Base.metadata.create_all(engine)
    cherrypy.config.update({
        'SOCIAL_AUTH_USER_MODEL': 'pacifica.ingest.orm.User',
    })
    # this needs to be imported after cherrypy settings are applied.
    # pylint: disable=import-outside-toplevel
    from social_cherrypy.models import SocialBase
    SocialBase.metadata.create_all(engine)
    return 0


if __name__ == '__main__':
    main(sys_argv[1:])
