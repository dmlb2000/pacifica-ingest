#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Test ingest with good uploads of good and bad data."""
from __future__ import print_function, absolute_import
import requests
from cherrypy.test import helper
from .common_methods_test import try_good_upload
from .ingest_db_setup_test import IngestCPSetup
from .shwrapper_test import sh


class TestIngestUpload(IngestCPSetup, helper.CPWebCase):
    """Test the move ingest api."""

    bash = sh.Command('/bin/bash')

    def test_bad_job_id(self):
        """Test a bad job ID."""
        req = requests.get('http://127.0.0.1:8066/get_state?job_id=12345')
        self.assertEqual(req.status_code, 404)

    def test_good_upload(self):
        """Test the good upload."""
        try_good_upload(self, 'good', 'OK', 'ingest metadata', 100)

    def test_bad_project_upload(self):
        """Test if the metadata is down."""
        try_good_upload(self, 'bad-project', 'FAILED', 'Policy Validation', 0)

    def test_bad_hashsum_upload(self):
        """Test if the metadata is down."""
        try_good_upload(self, 'bad-hashsum', 'FAILED', 'ingest files', 0)

    def test_bad_metadata_upload(self):
        """Test if the metadata is down."""
        try_good_upload(self, 'bad-mimetype', 'FAILED', 'ingest metadata', 0)

    def test_bad_json_upload(self):
        """Test if the metadata is down."""
        try_good_upload(self, 'bad-json', 'FAILED', 'load metadata', 0)

    def test_bad_tarfile_upload(self):
        """Test if the metadata is down."""
        try_good_upload(self, 'bad-tarfile', 'FAILED', 'open tar', 0)
