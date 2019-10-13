#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Test module for the ingest python code."""
from os.path import join, realpath, dirname
from time import sleep
from json import loads
import requests


def check_upload_state(job_id, wait):
    """Get the upload state and return results."""
    sleep(wait)
    req = requests.get(
        'http://127.0.0.1:8066/get_state?job_id={}'.format(job_id))
    assert req.status_code == 200
    job_state = loads(req.text)
    return job_state


def try_assert_job_state(job_state, state, task, percent):
    """assert on the job state bits."""
    assert job_state['state'] == state
    assert job_state['task'] == task
    assert int(float(job_state['task_percent'])) == percent


# pylint: disable=too-many-arguments
def try_good_move(cls, mdfile, state, task, percent, wait=5):
    """Test the move and see if the state task and percent match."""
    md_file_path = (
        dirname(realpath(__file__)),
        'test_data', '{}.json'.format(mdfile)
    )
    with open(join(*md_file_path), 'r') as filefd:
        req = requests.post(
            'http://127.0.0.1:8066/move',
            data=filefd.read(),
            headers={'content-type': 'application/json'}
        )
        cls.assertEqual(req.status_code, 200)
        job_id = req.json()['job_id']
        job_state = check_upload_state(job_id, wait)
        try_assert_job_state(job_state, state, task, percent)


def try_good_upload(tarfile, state, task, percent, wait=5):
    """Test the upload and see if the state task and percent match."""
    tar_file_path = (
        dirname(realpath(__file__)),
        'test_data', '{}.tar'.format(tarfile)
    )
    with open(join(tar_file_path), 'rb') as filefd:
        req = requests.post(
            'http://127.0.0.1:8066/upload',
            data=filefd,
            headers={
                'Content-Type': 'application/octet-stream'
            }
        )
        assert req.status_code == 200
        job_state = check_upload_state(loads(req.text)['job_id'], wait)
        try_assert_job_state(job_state, state, task, percent)
