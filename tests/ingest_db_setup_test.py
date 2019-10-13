#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Test cart database setup class."""
import os
from unittest import TestCase
import threading
import cherrypy
from celery.bin.celery import main as celery_main
from peewee import SqliteDatabase
from pacifica.ingest.rest import error_page_default, Root
from pacifica.ingest.orm import IngestState, IngestStateSystem, DB


class IngestCPSetup(object):
    """Perform the common cherrypy setup."""

    PORT = 8066
    HOST = '127.0.0.1'
    url = 'http://{0}:{1}'.format(HOST, PORT)
    headers = {'content-type': 'application/json'}

    @classmethod
    def setup_server(cls):
        """Start all the services."""
        os.environ['INGEST_CPCONFIG'] = os.path.join(os.path.dirname(
            os.path.realpath(__file__)), '..', 'server.conf')
        cherrypy.config.update({'error_page.default': error_page_default})
        cherrypy.config.update(os.environ['INGEST_CPCONFIG'])
        cherrypy.tree.mount(Root(), '/', os.environ['INGEST_CPCONFIG'])

    # pylint: disable=invalid-name
    def setUp(self):
        """Setup the database with in memory sqlite."""
        DB.drop_tables([IngestState, IngestStateSystem])
        DB.create_tables([IngestState, IngestStateSystem])
        IngestStateSystem.get_or_create_version()

        def run_celery_worker():
            """Run the main solo worker."""
            return celery_main([
                'celery', '-A', 'pacifica.ingest.tasks', 'worker', '--pool', 'solo',
                '-l', 'info', '--quiet', '-b', 'redis://127.0.0.1:6379/0'
            ])

        self.celery_thread = threading.Thread(target=run_celery_worker)
        self.celery_thread.start()

    # pylint: disable=invalid-name
    def tearDown(self):
        """Tear down the test and remove local state."""
        try:
            celery_main([
                'celery', '-A', 'pacifica.ingest.tasks', 'control',
                '-b', 'redis://127.0.0.1:6379/0', 'shutdown'
            ])
        except SystemExit:
            pass
        self.celery_thread.join()
        try:
            celery_main([
                'celery', '-A', 'pacifica.ingest.tasks', '-b', 'redis://127.0.0.1:6379/0',
                '--force', 'purge'
            ])
        except SystemExit:
            pass


class IngestDBSetup(TestCase):
    """Contain all the tests for the Cart Interface."""

    # pylint: disable=invalid-name
    def setUp(self):
        """Setup the database with in memory sqlite."""
        self._db = SqliteDatabase('file:cachedb?mode=memory&cache=shared')
        for model in [IngestState, IngestStateSystem]:
            model.bind(self._db, bind_refs=False, bind_backrefs=False)
        self._db.connect()
        self._db.create_tables([IngestState, IngestStateSystem])
        IngestStateSystem.get_or_create_version()

    def tearDown(self):
        """Tear down the database."""
        self._db.drop_tables([IngestState, IngestStateSystem])
        self._db.close()
        self._db = None
        DB.bind([IngestState, IngestStateSystem])
    # pylint: enable=invalid-name
