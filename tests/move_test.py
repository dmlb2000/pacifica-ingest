#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Test ingest with good uploads of good and bad data."""
from __future__ import print_function, absolute_import
import os
import json
import hashlib
from contextlib import contextmanager
from tempfile import NamedTemporaryFile
from tempfile import TemporaryDirectory
from six import ensure_binary
import requests
from .common_methods_test import try_good_move, check_upload_state, try_assert_job_state


def test_good_move():
    """Test the good move."""
    try_good_move('move-md', 'OK', 'ingest metadata', 100)


def test_bad_file_move():
    """Test the bad file path move."""
    try_good_move('bad-move-md', 'FAILED', 'move files', 0)


@contextmanager
def create_temp_files(temp_dir, num_files=100):
    """Create lots of temporary files and save them."""
    file_list = []
    for file_index in range(num_files):
        file_name = ''
        file_hash = ''
        with NamedTemporaryFile(dir=temp_dir, suffix='.txt', delete=False) as temp_file:
            temp_file.write(ensure_binary('This is a temp file {}.'.format(file_index)))
            file_name = temp_file.name
        with open(file_name) as file_desc:
            file_hash = hashlib.sha1()
            file_hash.update(ensure_binary(file_desc.read()))
            file_hash = file_hash.hexdigest()
        file_list.append({
            'ctime': 'Tue Nov 29 14:09:05 PST 2016',
            'destinationTable': 'Files',
            'hashsum': file_hash,
            'hashtype': 'sha1',
            'mimetype': 'text/plain',
            'mtime': 'Tue Nov 29 14:09:05 PST 2016',
            'name': 'tempfile.{}.txt'.format(file_index),
            'size': os.stat(file_name).st_size,
            'source': file_name,
            'subdir': 'data/a/b/'
        })
    yield file_list


def test_big_move():
    """Test should create a large move and verify speed."""
    with open(os.path.join('test_data', 'move-md.json'), 'r') as md_fd:
        md_data = json.loads(md_fd.read())
        md_data.pop()
    with TemporaryDirectory() as temp_dir:
        with create_temp_files(temp_dir) as file_list:
            md_data.extend(file_list)
            req = requests.post(
                'http://127.0.0.1:8066/move',
                json=md_data,
                headers={'content-type': 'application/json'}
            )
            assert req.status_code == 200
            job_id = req.json()['job_id']
            job_state = check_upload_state(job_id, 15)
            try_assert_job_state(job_state, 'OK', 'ingest metadata', 100)
