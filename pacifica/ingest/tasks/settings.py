#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Celery Settings Module."""
from os import getenv
from os.path import join
from argparse import Namespace
from collections import defaultdict
from pacifica.auth import create_configparser
from ..config import ingest_config

configparser = create_configparser(
    Namespace(config=getenv('CONFIG_FILE', 'config.ini')),
    ingest_config
)
_broker_dir = configparser.get('celery', 'filesystem_broker_dir')
broker_transport_options=defaultdict(
    data_folder_in=join(_broker_dir, 'out'),
    data_folder_out=join(_broker_dir, 'out'),
    data_folder_processed=join(_broker_dir, 'processed')
)
celery_settings = defaultdict(
    loglevel='INFO',
    traceback=True,
    broker_url=configparser.get('celery', 'broker_url'),
    result_backend=configparser.get('celery', 'backend_url'),
)
if 'filesystem' in celery_settings['broker_url']:
    celery_settings['broker_transport_options'] = broker_transport_options
    celery_settings['task_serializer'] = 'json'
    celery_settings['result_serializer'] = 'json'
    celery_settings['accept_content'] = ['json']
    celery_settings['result_persistent'] = False

print(celery_settings)

__all__ = ['celery_settings']
