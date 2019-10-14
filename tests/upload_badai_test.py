#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Test ingest with a disabled archive interface."""
from __future__ import print_function, absolute_import
from os.path import join, dirname, realpath
from cherrypy.test import helper
from .common_methods_test import try_good_upload, try_good_move
from .ingest_db_setup_test import IngestCPSetup
from .shwrapper_test import sh


class TestIngestBadAI(IngestCPSetup, helper.CPWebCase):
    """Test the move ingest api."""

    bash = sh.Command('/bin/bash')

    # this is a long name but descriptive.
    # pylint: disable=invalid-name
    def test_bad_archiveinterface_upload(self):
        """Test if the archive interface is down."""
        self.bash('-c', join(dirname(realpath(__file__)), 'build-tars.sh'))
        self.bash('-c', 'sudo service archiveinterface stop')
        try_good_upload(self, 'good', 'FAILED', 'ingest files', 0, 10)
        self.bash('-c', 'sudo service archiveinterface start')
    # pylint: enable=invalid-name

    def test_bad_ai_move(self):
        """Test the good move."""
        self.bash('-c', join(dirname(realpath(__file__)), 'build-tars.sh'))
        self.bash('-c', 'sudo service archiveinterface stop')
        try_good_move(self, 'move-md', 'FAILED', 'move files', 0, 10)
        self.bash('-c', 'sudo service archiveinterface start')
