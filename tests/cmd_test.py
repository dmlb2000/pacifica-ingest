#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Test script to run the command interface for testing."""
import sys
import os
from unittest import TestCase
from tempfile import mkdtemp
from shutil import rmtree
try:
    import sh
except ImportError:
    import pbs

    class Sh(object):
        """Sh style wrapper."""

        def __getattr__(self, attr):
            """Return command object like sh."""
            return pbs.Command(attr)

        # pylint: disable=invalid-name
        @staticmethod
        def Command(attr):
            """Return command object like sh."""
            return pbs.Command(attr)
    sh = Sh()
import peewee
from pacifica.ingest.__main__ import cmd, main
from pacifica.ingest.orm import DB, IngestState, IngestStateSystem


class TestAdminCmdBase(TestCase):
    """Test base class to setup update conditions."""

    virtualenv_dir = mkdtemp()

    @classmethod
    def setUpClass(cls):
        """Setup a virtualenv and install the original version."""
        python_cmd = sh.Command(sys.executable)
        python_exe = os.path.basename(sys.executable)
        python_cmd('-m', 'virtualenv', '--python', sys.executable, cls.virtualenv_dir)
        python_venv_cmd = None
        for exe_dir in ['bin', 'Scripts']:
            fpath = os.path.join(cls.virtualenv_dir, exe_dir, python_exe)
            if os.path.isfile(fpath) and os.access(fpath, os.X_OK):
                python_venv_cmd = sh.Command(fpath)
        python_venv_cmd('-m', 'pip', 'install', 'pacifica-ingest==0.2.0', 'psycopg2')
        python_venv_cmd('-c', 'from pacifica.ingest.orm import database_setup; database_setup();')

    @classmethod
    def tearDownClass(cls):
        """Remove the virtualenv dir."""
        rmtree(cls.virtualenv_dir)
        cmd(['dbsync'])
        DB.drop_tables([IngestState, IngestStateSystem])
        DB.close()


class TestAdminCmd(TestAdminCmdBase):
    """Test the admin commands for error conditions."""

    def test_dbchk(self):
        """Test that dbchk doesn't work."""
        self.assertEqual(cmd(['dbchk']), -1)

    def test_dbchk_equal(self):
        """Test that dbchk doesn't work."""
        self.assertEqual(cmd(['dbchk', '--equal']), -1)

    def test_main(self):
        """Test that dbchk doesn't work."""
        with self.assertRaises(peewee.OperationalError):
            main(['--stop-after-a-moment'])


class TestAdminCmdSync(TestAdminCmdBase):
    """Test the database upgrade scripting."""

    def test_main(self):
        """Test that dbchk doesn't work."""
        self.assertEqual(cmd(['dbsync']), 0)
        self.assertEqual(cmd(['dbsync']), 0)
        hit_exception = False
        try:
            main(['--stop-after-a-moment', '--cpconfig', 'server.conf'])
        # pylint: disable=broad-except
        except Exception:
            hit_exception = True
        self.assertFalse(hit_exception)
