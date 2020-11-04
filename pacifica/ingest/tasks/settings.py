#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Celery Settings Module."""
from os import getenv
from os.path import join
from argparse import Namespace
import collections
from pacifica.auth import create_configparser

configparser = create_configparser(Namespace(config=getenv('CONFIG_FILE', 'config.ini')))
_broker_dir = configparser.get('celery', 'filesystem_broker_dir')
celery_settings = collections.defaultdict(
    loglevel='INFO',
    traceback=True,
    broker=configparser.get('celery', 'broker_url'),
    backend=configparser.get('celery', 'backend_url'),
    broker_transport_options=collections.defaultdict(
        data_folder_in=join(_broker_dir, 'out'),
        data_folder_out=join(_broker_dir, 'out'),
        data_folder_processed=join(_broker_dir, 'processed')
    ),
    result_persistent=False,
    task_serializer='json',
    result_serializer='json',
    accept_content=['json']
)

__all__ = ['celery_settings']
