#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Module that contains all the amqp tasks that support the ingest infrastructure."""
from __future__ import absolute_import, print_function
import os
import traceback
import requests
from celery import Celery
from .tarutils import open_tar, MetaParser, TarIngester, patch_files
from .orm import update_state
from .config import get_config


INGEST_APP = Celery(
    'ingest',
    broker=get_config().get('celery', 'broker_url'),
    backend=get_config().get('celery', 'backend_url')
)


class IngestException(Exception):
    """Ingest class exception."""


def ingest_check_tarfile(job_id, filepath):
    """Check the ingest tarfile and return state or set it properly."""
    update_state(job_id, 'OK', 'open tar', 0)
    tar = open_tar(filepath)
    if tar is None:
        update_state(job_id, 'FAILED', 'open tar',
                     0, 'Failed to open tarfile.')
        raise IngestException()
    update_state(job_id, 'OK', 'open tar', 100)
    return tar


def move_metadata_parser(job_id, metafile):
    """Ingest the metadata and set the state appropriately."""
    update_state(job_id, 'OK', 'load metadata', 0)
    meta = MetaParser()
    meta.read_meta(metafile, job_id)
    update_state(job_id, 'OK', 'load metadata', 100)
    return meta


def ingest_metadata_parser(job_id, tar):
    """Ingest the metadata and set the state appropriately."""
    update_state(job_id, 'OK', 'load metadata', 0)
    meta = MetaParser()
    try:
        meta.load_meta(tar, job_id)
    # pylint: disable=broad-except
    except Exception as ex:
        update_state(job_id, 'FAILED', 'load metadata', 0, str(ex))
        raise IngestException()
    update_state(job_id, 'OK', 'load metadata', 100)
    return meta


def ingest_policy_check(job_id, meta_str, authed_user):
    """Ingest check to validate metadata at policy."""
    success, exception = validate_meta(meta_str, authed_user)
    if not success:
        update_state(job_id, 'FAILED', 'Policy Validation', 0, exception)
        raise IngestException()
    update_state(job_id, 'OK', 'Policy Validation', 100)


def move_files(job_id, meta_obj):
    """Move the files to the archive interface."""
    update_state(job_id, 'OK', 'move files', 0)
    try:
        patch_files(meta_obj)
    # pylint: disable=broad-except
    except Exception as ex:
        # rollback files
        stack_dump = traceback.format_exc()
        update_state(job_id, 'FAILED', 'move files', 0,
                     u'{}\n{}'.format(stack_dump, str(ex)))
        raise IngestException()
    update_state(job_id, 'OK', 'move files', 100)


def ingest_files(job_id, ingest_obj):
    """Ingest the files to the archive interface."""
    update_state(job_id, 'OK', 'ingest files', 0)
    try:
        ingest_obj.ingest()
    # pylint: disable=broad-except
    except Exception as ex:
        # rollback files
        stack_dump = traceback.format_exc()
        update_state(job_id, 'FAILED', 'ingest files', 0,
                     u'{}\n{}'.format(stack_dump, str(ex)))
        raise IngestException()
    update_state(job_id, 'OK', 'ingest files', 100)


def ingest_metadata(job_id, meta):
    """Ingest metadata to the metadata service."""
    update_state(job_id, 'OK', 'ingest metadata', 0)
    success, exception = meta.post_metadata()
    if not success:
        # rollback files
        update_state(job_id, 'FAILED', 'ingest metadata', 0, str(exception))
        raise IngestException()
    update_state(job_id, 'OK', 'ingest metadata', 100)


@INGEST_APP.task(ignore_result=False)
def move(job_id, filepath, authed_user):
    """Move a MD bundle into the archive."""
    try:
        meta = move_metadata_parser(job_id, filepath)
        ingest_policy_check(job_id, meta.meta_str, authed_user)
        move_files(job_id, meta)
        ingest_metadata(job_id, meta)
        os.unlink(filepath)
    except IngestException:
        return


@INGEST_APP.task(ignore_result=False)
def ingest(job_id, filepath, authed_user):
    """Ingest a tar bundle into the archive."""
    try:
        tar = ingest_check_tarfile(job_id, filepath)
        meta = ingest_metadata_parser(job_id, tar)
        ingest_obj = TarIngester(tar, meta)
        ingest_policy_check(job_id, meta.meta_str, authed_user)
        ingest_files(job_id, ingest_obj)
        ingest_metadata(job_id, meta)
        tar.close()
        os.unlink(filepath)
    except IngestException:
        return


def validate_meta(meta_str, authed_user):
    """Validate metadata."""
    try:
        ingest_policy_url = get_config().get('policy', 'ingest_url')
        headers = {
            'content-type': 'application/json',
            get_config().get('ingest', 'auth_header'): authed_user
        }
        session = requests.session()
        retry_adapter = requests.adapters.HTTPAdapter(max_retries=5)
        session.mount('http://', retry_adapter)
        session.mount('https://', retry_adapter)
        req = session.post(ingest_policy_url, headers=headers, data=meta_str)

        req_json = req.json()
        if req_json['status'] == 'success':
            return True, ''
        return False, '{} ({})'.format(req_json['message'], req_json['traceback'])
    # pylint: disable=broad-except
    except Exception as ex:
        return False, ex
    # pylint: enable=broad-except
