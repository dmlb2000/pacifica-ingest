#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Index server unit and integration tests."""
from __future__ import absolute_import
import os
from tempfile import mkstemp
import requests
from pacifica.ingest.orm import IngestState, update_state, read_state
from pacifica.ingest.orm import IngestStateSystem, OrmSync
from pacifica.ingest.utils import get_unique_id
from pacifica.ingest.tarutils import open_tar
from pacifica.ingest.tarutils import MetaParser
from pacifica.ingest.tarutils import TarIngester
from pacifica.ingest.tarutils import FileIngester
from pacifica.ingest.tasks import ingest
from .ingest_db_setup_test import IngestDBSetup


class IngestServerUnitTests(IngestDBSetup):
    """Ingest server unit and integration tests."""

    def test_file_ingester(self):
        """Test the FileIngester class."""
        FileIngester('sha1', 'fakehashsum', '1')
        hit_exception = False
        try:
            FileIngester('badfunc', 'fakehashsum', '1')
        except ValueError:
            hit_exception = True
        self.assertTrue(hit_exception)

    def test_load_meta(self):
        """Test sucking metadata from uploader and configuring it in a dictionary suitable to blob to meta ingest."""
        tar = open_tar('test_data/good.tar')

        meta = MetaParser()
        meta.load_meta(tar, 1)
        self.assertTrue(meta)

    def test_tasks(self):
        """Test the ingest task."""
        job_id = get_unique_id(1, 'upload_job')

        ingest(job_id, 'test_data/good.tar', 'root')
        self.assertTrue(job_id)

    def test_post_metadata(self):
        """Test sucking metadata from uploader and configuring it in a dictionary suitable to blob to meta ingest."""
        tar = open_tar('test_data/good.tar')
        meta = MetaParser()
        meta.load_meta(tar, 1)
        success, exception = meta.post_metadata()
        self.assertTrue(success)
        self.assertFalse(exception)
        tar = open_tar('test_data/bad-mimetype.tar')
        meta = MetaParser()
        meta.load_meta(tar, 2)
        success, exception = meta.post_metadata()
        self.assertFalse(success)
        self.assertTrue(exception)

    def test_down_metadata(self):
        """Test a failed upload of the metadata."""
        tar = open_tar('test_data/good.tar')
        meta = MetaParser()

        def bad_put(*args, **kwargs):  # pylint: disable=unused-argument
            """bad put to the metadata server."""
            raise requests.HTTPError()
        meta.session.put = bad_put
        meta.load_meta(tar, 1)
        success, exception = meta.post_metadata()
        self.assertFalse(success)
        self.assertTrue(exception)

    def test_ingest_tar(self):
        """Test moving individual files to the archive files are validated inline with the upload."""
        tar = open_tar('test_data/good.tar')
        meta = MetaParser()
        meta.load_meta(tar, 1)

        tingest = TarIngester(tar, meta)
        # validate archive process

        # if not valid:
        #     rollback()
        # success = MetaUpload()
        tingest.ingest()
        self.assertTrue(tingest)

    def test_update_state(self):
        """Test return and update of unique index."""
        rwfd, fname = mkstemp()
        os.close(rwfd)
        test_object = IngestState.create(
            job_id=999,
            state='ERROR',
            task='unbundling',
            task_percent=42.3
        )
        self.assertEqual(test_object.job_id, 999)
        IngestState.database_close()
        update_state(999, 'WORKING', 'validating', 33.2)
        record = read_state(999)
        self.assertEqual(record.state, 'WORKING')
        self.assertEqual(record.task, 'validating')
        self.assertEqual(float(record.task_percent), 33.2)
        record = read_state(None)
        self.assertEqual(record.state, 'DATA_ACCESS_ERROR')
        self.assertEqual(record.task, 'read_state')
        self.assertEqual(record.task_percent, 0)
        os.unlink(fname)

    def test_no_table_goc_version(self):
        """Test the get or create version with no table."""
        OrmSync.dbconn_blocking()
        OrmSync.update_tables()
        IngestStateSystem.drop_table()
        major, minor = IngestStateSystem.get_or_create_version()
        self.assertEqual(major, 0)
        self.assertEqual(minor, 0)

    def test_update_tables_twice(self):
        """Test updating tables twice to verify completeness."""
        hit_exception = False
        try:
            OrmSync.dbconn_blocking()
            OrmSync.update_tables()
            OrmSync.update_tables()
        # pylint: disable=broad-except
        except Exception:
            hit_exception = True
        # pylint: enable=broad-except
        self.assertFalse(hit_exception)
