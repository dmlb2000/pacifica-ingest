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
    configparser.set('ingest', 'transfer_size', getenv(
        'TRANSFER_SIZE', '4 Mb'))
    configparser.set('ingest', 'transfer_backend', getenv(
        'TRANSFER_BACKEND', 'ssh'))
    configparser.set('ingest', 'upload_path', getenv(
        'UPLOAD_PATH', '/tmp/upload'))
    configparser.set('ingest', 'move_path', getenv(
        'MOVE_PATH', '/tmp/move'))
    configparser.set('ingest', 'session_path', getenv(
        'SESSION_PATH', '/tmp/session'))
    configparser.set('ingest', 'ssh_auth_keys_dir', getenv(
        'SSH_AUTH_KEYS_DIR', '/etc/ssh/keys'))
    configparser.add_section('uniqueid')
    configparser.set('uniqueid', 'url', getenv(
        'UNIQUEID_URL', 'http://127.0.0.1:8051'))
    configparser.add_section('policy')
    # one of 'jsonschema', 'none'
    configparser.set('policy', 'type', getenv(
        'POLICY_TYPE', 'jsonschema'))
    configparser.set('policy', 'jsonschema_file', getenv(
        'POLICY_JSONSCHEMA_FILE', 'policy_jsonschema.json'))
    configparser.add_section('archiveinterface')
    configparser.set('archiveinterface', 'embedded', getenv(
        'ARCHIVEINTERFACE_EMBEDDED', 'True'))
    configparser.set('archiveinterface', 'use_id2filename', getenv(
        'ARCHIVEINTERFACE_ID2FILENAME', 'True'))
    configparser.set('archiveinterface', 'prefix', getenv(
        'ARCHIVEINTERFACE_PREFIX', '/tmp/archive'))
    configparser.set('archiveinterface', 'url', getenv(
        'ARCHIVEINTERFACE_URL', 'http://127.0.0.1:8080'))
    configparser.add_section('metadata')
    # one of 'drupal_jsonapi', 'none'
    configparser.set('metadata', 'type', getenv(
        'METADATA_TYPE', 'drupal_jsonapi'))
    configparser.set('metadata', 'drupal_url', getenv(
        'METADATA_DRUPAL_URL', 'http://127.0.0.1/jsonapi'))
    configparser.set('metadata', 'drupal_user', getenv(
        'METADATA_DRUPAL_USER', 'admin'))
    configparser.set('metadata', 'drupal_key', getenv(
        'METADATA_DRUPAL_KEY', 'adminsuperkey'))
    configparser.set('metadata', 'drupal_content_type', getenv(
        'METADATA_DRUPAL_CONTENT_TYPE', 'data_upload'))
    configparser.set('metadata', 'drupal_field', getenv(
        'METADATA_DRUPAL_FIELD', 'field_file_data'))
    configparser.add_section('database')
    configparser.set('database', 'db_url', getenv(
        'DATABASE_CONNECT_URL', 'sqlite:///db.sqlite3'))
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
