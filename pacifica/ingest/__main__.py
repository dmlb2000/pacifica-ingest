#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Ingest module."""
import json
from sys import argv as sys_argv
from time import sleep
from threading import Thread
from argparse import ArgumentParser, SUPPRESS
import cherrypy
from pacifica.auth import pacifica_auth_arguments, error_page_default, social_settings
from pacifica.auth.root import Root
from .rest import UploadSession
from .tasks import get_db_session
from .orm import User, Base, Session, SessionEncoder
from .globals import CONFIG_FILE


def stop_later(doit=False):
    """Used for unit testing stop after 60 seconds."""
    if not doit:  # pragma: no cover
        return

    def sleep_then_exit():
        """
        Sleep for 90 seconds then call cherrypy exit.

        Hopefully this is long enough for the end-to-end tests to finish
        """
        sleep(120)
        cherrypy.engine.exit()
    sleep_thread = Thread(target=sleep_then_exit)
    sleep_thread.daemon = True
    sleep_thread.start()


def main(argv=None):
    """Main method to start the httpd server."""
    parser = ArgumentParser(description='Run the cart server.')
    parser.add_argument('-c', '--config', metavar='CONFIG', type=str,
                        default=CONFIG_FILE, dest='config',
                        help='ingest config file')
    parser.add_argument('-p', '--port', metavar='PORT', type=int,
                        default=8066, dest='port',
                        help='port to listen on')
    parser.add_argument('-a', '--address', metavar='ADDRESS',
                        default='0.0.0.0', dest='address',
                        help='address to listen on')
    parser.add_argument('--stop-after-a-moment', help=SUPPRESS,
                        default=False, dest='stop_later',
                        action='store_true')
    pacifica_auth_arguments(parser)
    args = parser.parse_args(argv)
    social_settings(args, User, 'pacifica.ingest.orm.User')
    stop_later(args.stop_later)
    common_config = {
        '/': {
            'error_page.default': error_page_default,
            'request.dispatch': cherrypy.dispatch.MethodDispatcher()
        }
    }
    cherrypy.tree.mount(UploadSession(), '/session', config=common_config)
    cherrypy.config.update({
        'server.socket_host': args.address,
        'server.socket_port': args.port
    })
    cherrypy.quickstart(Root(args.sa_module, args.app_dir), '/', config={'/': {}})


def cmd(argv=None):
    """Command line admin tool for managing ingest."""
    parser = ArgumentParser(description='Admin command line tool.')
    parser.add_argument(
        '-c', '--config', metavar='CONFIG', type=str, default=CONFIG_FILE,
        dest='config', help='ingest config file'
    )
    parser.set_defaults(func=lambda x: parser.print_help())
    subparsers = parser.add_subparsers(help='sub-command help')
    setup_job_subparser(subparsers)
    setup_db_subparser(subparsers)
    args = parser.parse_args(argv)
    return args.func(args)


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
    pacifica_auth_arguments(db_parser)
    db_parser.set_defaults(func=dbsync)


def job_output(args):
    """Dump the jobs requested from the command line."""
    sessions = []
    # pylint: disable=invalid-name
    with get_db_session() as db:
        for job_uuid in args.job_uuids:
            # pylint: disable=no-member
            sessions.append(db.query(Session).filter_by(uuid=job_uuid).first())
    print(json.dumps(sessions, sort_keys=True, indent=4, cls=SessionEncoder))
    return 0


def dbsync(args):
    """Create/Update the database schema to current code."""
    Base.metadata.create_all(args.engine)
    cherrypy.config.update({
        'SOCIAL_AUTH_USER_MODEL': 'pacifica.ingest.orm.User',
    })
    # this needs to be imported after cherrypy settings are applied.
    # pylint: disable=import-outside-toplevel
    from social_cherrypy.models import SocialBase
    SocialBase.metadata.create_all(args.engine)
    return 0


if __name__ == '__main__':
    main(sys_argv[1:])
