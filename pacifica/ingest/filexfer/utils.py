#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Utility methods for managing files."""
from os import makedirs, getenv
from shutil import move
from os.path import getmtime, getsize, join, exists, normpath, dirname
from datetime import datetime
import hashlib
import requests
from pacifica.archiveinterface.backends.factory import ArchiveBackendFactory


def parse_size(size):
    """Parse size string to integer."""
    units = {
        'B': 1, 'KB': 10**3, 'MB': 10**6, 'GB': 10**9, 'TB': 10**12,
        'b': 1, 'Kb': 1024, 'Mb': 1024**2, 'Gb': 1024**3, 'Tb': 1024**4
    }
    number, unit = [string.strip() for string in size.split()]
    return int(float(number)*units[unit])


def hash_local_file(configparser, filepath):
    """Hash sum a local file and return hex digest."""
    hashtype = configparser.get('ingest', 'hashtype')
    xfersize = parse_size(configparser.get('ingest', 'transfer_size'))
    checksum = getattr(hashlib, hashtype)()
    with open(filepath, 'rb') as fd:
        checksum.update(fd.read(xfersize))
    return checksum.hexdigest()


def get_unique_id(configparser, id_range, mode='file'):
    """Return a unique job id from the id server."""
    uniqueid_url = configparser.get('uniqueid', 'url')
    resp = requests.get(
        '{}/getid'.format(uniqueid_url),
        params={'range': id_range, 'mode': mode}
    )
    assert resp.status_code == 200
    return resp.json()


def move_file(configparser, file_id, filepath):
    """Move the file into the archive."""
    backend = ArchiveBackendFactory().get_backend_archive(
        getenv('PAI_BACKEND_TYPE', 'posix'),
        configparser.get('archiveinterface', 'prefix')
    )
    backend.patch(file_id, filepath)


def _int_move_file(configparser, file_id, filepath):
    """Move the file into the archive."""
    archive_url = configparser.get('archiveinterface', 'url')
    resp = requests.patch(
        '{}/{}'.format(archive_url, file_id),
        json={'path': filepath}
    )
    assert resp.status_code == 200


def remote_file(configparser, file_id, filepath):
    """Send the file remotely to archive interface."""
    archive_url = configparser.get('archiveinterface', 'url')
    resp = requests.put(
        '{}/{}'.format(archive_url, file_id),
        data=open(filepath, 'r'),
        headers={
            'Last-Modified': datetime.fromtimestamp(getmtime(filepath)).isoformat(),
            'Content-Type': 'application/octet-stream',
            'Content-Length': str(getsize(filepath)),
        }
    )
    assert resp.status_code == 200


def send_file(configparser, file_id, filepath):
    """Send the file to the archive interface."""
    if configparser.getboolean('archiveinterface', 'embedded'):
        return move_file(configparser, file_id, filepath)
    return remote_file(configparser, file_id, filepath)
