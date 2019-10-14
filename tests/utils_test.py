#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Test ingest."""
import os
import mock
import peewee
import requests
from cherrypy.test import helper
from pacifica.ingest.orm import OrmSync, IngestState
from .ingest_db_setup_test import IngestCPSetup


class TestIngestUpload(IngestCPSetup, helper.CPWebCase):
    """Test the move ingest api."""

    @mock.patch.object(IngestState, 'database_connect')
    def test_bad_db_connection(self, mock_is_table_exists):
        """Test a failed db connection."""
        mock_is_table_exists.side_effect = peewee.OperationalError(
            mock.Mock(), 'Error')
        hit_exception = False
        os.environ['DATABASE_CONNECT_ATTEMPTS'] = '1'
        os.environ['DATABASE_CONNECT_WAIT'] = '1'
        try:
            OrmSync.dbconn_blocking()
        except peewee.OperationalError:
            hit_exception = True
        self.assertTrue(hit_exception)

    def test_rest_root_status(self):
        """Test the root level status page."""
        resp = requests.get('http://127.0.0.1:8066')
        self.assertEqual(resp.status_code, 200, 'Status code should be 200 OK')
        self.assertTrue('message' in resp.json(), 'Status should be object with message key.')
        self.assertEqual(resp.json()['message'], 'Pacifica Ingest Up and Running', 'message should be specific.')
