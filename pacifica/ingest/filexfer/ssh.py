#!/usr/bin/python
# -*- coding: utf-8 -*-
"""File transfer ssh backend module."""
from os import unlink, mkdir, chown, chmod
from os.path import join, isfile
from shutil import rmtree
from pwd import getpwnam
import string
import random
from json import dumps, loads
from subprocess import run
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from .abstract import FileXFerBase
from ..config import get_config
from ..orm import Session


class FileXFerSSH(FileXFerBase):
    """
    Backend class to implement ssh file transfers.

    This class does require the python service have root permissions
    and run on a supported platform.
    """

    def __init__(self):
        """Create and assign instance variables."""
        self.session_path = get_config().get('ingest', 'session_path')
        self.username = None
        self.ssh_auth_keys_dir = get_config().get('ingest', 'ssh_auth_keys_dir')

    def generate_user_auth(self, session: Session) -> None:
        """Generate the ssh authentication username and password."""
        key = rsa.generate_private_key(
            backend=default_backend(),
            public_exponent=65537,
            key_size=4096
        )
        public_key = key.public_key().public_bytes(
            serialization.Encoding.OpenSSH,
            serialization.PublicFormat.OpenSSH
        )
        pem = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )
        self.username = random.choices(string.ascii_lowercase + string.digits, k=30)
        session.user_auth = dumps({
            'username': ''.join(self.username),
            'private_key': pem.decode('utf-8'),
            'public_key': public_key.decode('utf-8')
        })

    def create_session(self, session: Session) -> None:
        """Create local user and directory for them to upload."""
        user_auth = loads(session.user_auth)
        home_dir = join(self.session_path, self.username)
        run(
            [
                '/usr/sbin/useradd',
                '--home-dir',
                home_dir,
                '--no-create-home',
                '--gid',
                'sftponly',
                '--shell',
                '/sbin/nologin',
                self.username
            ],
            check=True
        )
        user_pwinfo = getpwnam(self.username)
        upload_dir = join(home_dir, 'upload')
        mkdir(home_dir)
        mkdir(upload_dir)
        chown(home_dir, 0, user_pwinfo.pw_gid)
        chmod(home_dir, 0o750)
        chown(upload_dir, user_pwinfo.pw_uid, user_pwinfo.pw_gid)
        chmod(upload_dir, 0o700)
        config_filename = join(self.ssh_auth_keys_dir, self.username)
        with open(config_filename, 'w') as file_fd:
            file_fd.write('{}\n'.format(user_auth['public_key']))
        user_pwinfo = getpwnam(self.username)
        chown(config_filename, user_pwinfo.pw_uid, user_pwinfo.pw_gid)
        chmod(config_filename, 0o400)

    def delete_session(self, session: Session) -> None:
        """Delete a user session."""
        user_auth = loads(session.user_auth)
        username = user_auth['username']
        config_filename = join(self.ssh_auth_keys_dir, self.username)
        home_dir = join(self.session_path, self.username)
        if isfile(config_filename):
            unlink(config_filename)
        rmtree(home_dir, ignore_errors=True)
        run(
            [
                '/usr/sbin/userdel',
                username
            ],
            check=True
        )
