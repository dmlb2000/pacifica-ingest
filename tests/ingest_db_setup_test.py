#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Test cart database setup class."""
from unittest import TestCase
from peewee import SqliteDatabase
from pacifica.ingest.orm import IngestState, IngestStateSystem, DB


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
