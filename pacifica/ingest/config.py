#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Configuration reading and validation module."""
from os import getenv
from configparser import ConfigParser as SafeConfigParser
from pacifica.ingest.globals import CONFIG_FILE


def get_config():
    """Return the ConfigParser object with defaults set."""
    configparser = SafeConfigParser()
    configparser.add_section('ingest')
    configparser.set('ingest', 'auth_header', getenv(
        'INGEST_AUTH_HEADER', 'X-Http-Authed-User'))
    configparser.set('ingest', 'default_user', getenv(
        'INGEST_DEFAULT_USER', 'root'))
    configparser.set('ingest', 'transfer_size', getenv(
        'TRANSFER_SIZE', '4 Mb'))
    configparser.set('ingest', 'volume_path', getenv(
        'VOLUME_PATH', '/tmp'))
    configparser.add_section('uniqueid')
    configparser.set('uniqueid', 'url', getenv(
        'UNIQUEID_URL', 'http://127.0.0.1:8051'))
    configparser.add_section('policy')
    configparser.set('policy', 'ingest_url', getenv(
        'POLICY_INGEST_URL', 'http://127.0.0.1:8181/ingest'))
    configparser.add_section('archiveinterface')
    configparser.set('archiveinterface', 'url', getenv(
        'ARCHIVEINTERFACE_URL', 'http://127.0.0.1:8080'))
    configparser.add_section('metadata')
    configparser.set('metadata', 'ingest_url', getenv(
        'METADATA_INGEST_URL', 'http://127.0.0.1:8121/ingest'))
    configparser.add_section('database')
    configparser.set('database', 'peewee_url', getenv(
        'PEEWEE_URL', 'sqliteext:///db.sqlite3'))
    configparser.set('database', 'connect_attempts', getenv(
        'DATABASE_CONNECT_ATTEMPTS', '10'))
    configparser.set('database', 'connect_wait', getenv(
        'DATABASE_CONNECT_WAIT', '20'))
    configparser.add_section('celery')
    configparser.set('celery', 'broker_url', getenv(
        'BROKER_URL', 'pyamqp://'))
    configparser.set('celery', 'backend_url', getenv(
        'BACKEND_URL', 'rpc://'))
    configparser.read(CONFIG_FILE)
    return configparser
