#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Test ingest with a disabled policy server."""
from __future__ import print_function, absolute_import
from os.path import join, dirname, realpath
from cherrypy.test import helper
from .common_methods_test import try_good_upload
from .shwrapper_test import sh
from .ingest_db_setup_test import IngestCPSetup


class TestIngestBadPolicy(IngestCPSetup, helper.CPWebCase):
    """Test the move ingest api."""

    bash = sh.Command('/bin/bash')

    def test_bad_policy_upload(self):
        """Test if the policy server is down."""
        self.bash('-c', join(dirname(realpath(__file__)), 'build-tars.sh'))
        self.bash('-c', 'sudo service policy stop')
        try_good_upload(self, 'good', 'FAILED', 'Policy Validation', 0, 10)
        self.bash('-c', 'sudo service policy start')
