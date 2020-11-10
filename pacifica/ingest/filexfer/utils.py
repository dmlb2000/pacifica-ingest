#!/usr/bin/python
"""Utility methods for managing files."""
from os.path import getmtime, getsize, join
from datetime import datetime
import hashlib
import requests
from pacifica.archiveinterface.id2filename import id2filename

def hash_local_file(configparser, filepath):
    hashtype = configparser.get('ingest', 'hashtype')
    xfersize = configparser.get('ingest', 'transfer_size')
    checksum = getattr(hashlib, hashtype)()
    with open(filepath, 'rb') as fd:
        checksum.update(fd.read(xfersize))
    return checksum.hexdigest()


def get_unique_id(configparser, id_range, mode='file'):
    """Return a unique job id from the id server."""
    uniqueid_url = configparser.get('uniqueid', 'url')
    resp = requests.get('{0}/getid', params={'range': id_range, 'mode': mode})
    assert resp.status_code == '200'
    return resp.json()


def move_file(configparser, file_id, filepath):
    """Move the file into the archive."""
    if configparser.getboolean('archiveinterface', 'use_id2filename'):
        file_id = id2filename(file_id)
    archive_root = configparser.get('archiveinterface', 'prefix')
    return os.rename(filepath, join(archive_root, file_id))


def remote_file(configparser, file_id, filepath):
    """Send the file remotely to archive interface."""
    archive_url = configparser.get('archiveinterface', 'url')
    resp = requests.put(
        '{}/{}'.format(archive_url, file_id),
        data=open(filepath, 'r'),
        headers={
            'Last-Modified': datetime.fromtimestamp(getmtime(filepath)).isoformat(),
            'Content-Type': 'application/octet-stream'
            'Content-Length': str(getsize(filepath))
        }
    )
    assert resp.status_code == 201


def send_file(configparser, file_id, filepath):
    """Send the file to the archive interface."""
    if configparser.getboolean('archiveinterface', 'embedded'):
        return move_file(configparser, file_id, filepath)
    return remote_file(configparser, file_id, filepath)
    