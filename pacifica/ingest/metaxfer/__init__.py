#!/usr/bin/python
"""Metadata transfer module."""
from configparser import ConfigParser
from importlib import import_module


class MetaXFerEngine:
    """Engine to call the appropriate backend implementation."""

    _class_map = {
        'drupal_jsonapi': 'MetaXFerDrupalJSONAPI'
    }

    def __init__(self, configparser: ConfigParser):
        """Create backend module."""
        modulename = '.{}'.format(configparser.get('metadata', 'type'))
        classname = self._class_map[configparser.get('metadata', 'type')]
        self._backend = getattr(import_module(modulename, 'pacifica.ingest.metaxfer'), classname)(configparser)

    def upload(self, db, session, filemeta):
        """Call the backend generate user auth."""
        return self._backend.upload(db, session, filemeta)