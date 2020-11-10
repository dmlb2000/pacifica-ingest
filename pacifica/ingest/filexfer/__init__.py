#!/usr/bin/python
# -*- coding: utf-8 -*-
"""File transfer backend module."""
from configparser import ConfigParser
from importlib import import_module


class FileXFerEngine:
    """Engine to call the appropriate backend implementation."""

    def __init__(self, configparser: ConfigParser):
        """Create backend module."""
        modulename = '.{}'.format(configparser.get('ingest', 'transfer_backend'))
        classname = 'FileXFer{}'.format(configparser.get('ingest', 'transfer_backend').upper())
        self._backend = getattr(import_module(modulename, 'pacifica.ingest.filexfer'), classname)(configparser)

    def generate_user_auth(self, session):
        """Call the backend generate user auth."""
        self._backend.generate_user_auth(session)

    def create_session(self, session):
        """Call the backend create session."""
        self._backend.create_session(session)

    def delete_session(self, session):
        """Call the backend delete session."""
        self._backend.delete_session(session)

    def commit_session(self, db, session):
        """Call the backend commit session."""
        return self._backend.commit_session(db, session)
