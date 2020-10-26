#!/usr/bin/python
# -*- coding: utf-8 -*-
"""File transfer backend module."""
from importlib import import_module
from ..config import get_config


class FileXFerEngine:
    """Engine to call the appropriate backend implementation."""

    def __init__(self):
        """Create backend module."""
        modulename = '.{}'.format(get_config().get('ingest', 'transfer_backend'))
        classname = 'FileXFer{}'.format(get_config().get('ingest', 'transfer_backend').upper())
        self._backend = getattr(import_module(modulename, 'pacifica.ingest.filexfer'), classname)()

    def generate_user_auth(self, session):
        """Call the backend generate user auth."""
        self._backend.generate_user_auth(session)

    def create_session(self, session):
        """Call the backend create session."""
        self._backend.create_session(session)

    def delete_session(self, session):
        """Call the backend delete session."""
        self._backend.delete_session(session)
