#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Celery Settings Module."""
from os.path import join
import collections
from ..config import get_config

_broker_dir = get_config().get('celery', 'filesystem_broker_dir')
celery_settings = collections.defaultdict(
    loglevel='INFO',
    traceback=True,
    broker=get_config().get('celery', 'broker_url'),
    backend=get_config().get('celery', 'backend_url'),
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
