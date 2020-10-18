#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Ingest module."""
import os
import getpass
from sys import argv as sys_argv
from time import sleep
from threading import Thread
from argparse import ArgumentParser, SUPPRESS
import cherrypy
from pacifica.auth import pacifica_auth_arguments, error_page_default, social_settings
from pacifica.auth.root import Root
from .rest import Session
from .tasks import move, ingest
from .orm import User
from .globals import CONFIG_FILE, CHERRYPY_CONFIG


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
                        default='localhost', dest='address',
                        help='address to listen on')
    parser.add_argument('--stop-after-a-moment', help=SUPPRESS,
                        default=False, dest='stop_later',
                        action='store_true')
    pacifica_auth_arguments(parser)
    args = parser.parse_args(argv)
    social_settings(args, User, 'pacifica.auth.user_model.User')
    stop_later(args.stop_later)
    common_config={
        '/': {
            'error_page.default': error_page_default,
            'request.dispatch': cherrypy.dispatch.MethodDispatcher()
        }
    }
    cherrypy.tree.mount(Session(), '/session', config=common_config)
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
    subparsers = parser.add_subparsers(help='sub-command help')
    setup_job_subparser(subparsers)
    setup_db_subparser(subparsers)
    setup_retry_subparser(subparsers)
    args = parser.parse_args(argv)
    return args.func(args)


def setup_job_subparser(subparsers):
    """Add the job subparser."""
    job_parser = subparsers.add_parser(
        'job', help='job help', description='manage jobs')
    for attr in ['job_id', 'state', 'task', 'task_percent', 'exception']:
        job_parser.add_argument(
            '--{}'.format(attr.replace('_', '-')),
            dest=attr,
            help='set the {}'.format(attr)
        )
    job_parser.set_defaults(func=update_wrapper)


def setup_db_subparser(subparsers):
    """Setup the dbsync subparser."""
    db_parser = subparsers.add_parser(
        'dbsync',
        description='Update or Create the Database.'
    )
    pacifica_auth_arguments(db_parser)
    db_parser.set_defaults(func=dbsync)


def setup_retry_subparser(subparsers):
    """Setup Ingest/Move retry subparsers."""
    retry_parser = subparsers.add_parser(
        'retry',
        description='Retry a move or ingest from a local file.'
    )
    retry_parser.add_argument(
        '--move', default=False,
        dest='move', action='store_true'
    )
    retry_parser.add_argument(
        '--path', dest='file_path',
        help='Path to the tar or json file on ingester.'
    )
    retry_parser.add_argument(
        '--username', dest='username', default=getpass.getuser(),
        help='Username of the actor performing the ingest.'
    )
    retry_parser.add_argument(
        '--job_id', dest='job_id',
        help='Job ID to use when ingesting.'
    )
    retry_parser.set_defaults(func=cli_ingest_move)


def update_wrapper(args):
    """Call update state with appropriate args."""
    return update_state(
        args.job_id,
        args.state,
        args.task,
        args.task_percent,
        args.exception
    )


def bool2cmdint(command_bool):
    """Convert a boolean to either 0 for true  or -1 for false."""
    if command_bool:
        return 0
    return -1


def dbsync(args):
    """Create/Update the database schema to current code."""
    Base.metadata.create_all(args.engine)
    # this needs to be imported after cherrypy settings are applied.
    # pylint: disable=import-outside-toplevel
    from social_cherrypy.models import SocialBase
    SocialBase.metadata.create_all(args.engine)
    return 0


def cli_ingest_move(args):
    """Call a local ingest or move action."""
    if args.move:
        return move(args.job_id, args.file_path, args.username)
    return ingest(args.job_id, args.file_path, args.username)


if __name__ == '__main__':
    main(sys_argv[1:])
