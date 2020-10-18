#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Global configuration options expressed in environment variables."""
from os import getenv
from os.path import expanduser, join

CONFIG_FILE = getenv('INGEST_CONFIG', join(
    expanduser('~'), '.pacifica-ingest', 'config.ini'))
