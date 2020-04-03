#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Little module to post data to Drupal via JSON:API."""
import json
import requests
from dateutil import parser
from .config import get_config


def _get_project_uuid(session, pac_proj_id):
    resp = session.get(
        '{}/node/pacifica_project'.format(get_config().get('drupal', 'url')),
        params={
            'fields[node--pacifica_project]': 'nid,uuid,field_pac_project_id',
            'filter[project-id][condition][path]': 'field_pac_project_id',
            'filter[project-id][condition][condition]': '=',
            'filter[project-id][condition][value]': pac_proj_id
        }
    )
    assert resp.status_code == 200
    return resp.json()['data'][0]['id']


def _get_user_uuid(session, pac_user_id):
    resp = session.get(
        '{}/node/pacifica_person'.format(get_config().get('drupal', 'url')),
        params={
            'fields[node--pacifica_person]': 'nid,uuid,field_pac_person_id',
            'filter[person-id][condition][path]': 'field_pac_person_id',
            'filter[person-id][condition][condition]': '=',
            'filter[person-id][condition][value]': pac_user_id
        }
    )
    assert resp.status_code == 200
    return resp.json()['data'][0]['id']


def _get_instrument_uuid(session, pac_inst_id):
    resp = session.get(
        '{}/node/pacifica_data_source'.format(get_config().get('drupal', 'url')),
        params={
            'fields[node--pacifica_data_source]': 'nid,uuid,field_pac_instrument_id',
            'filter[instrument-id][condition][path]': 'field_pac_instrument_id',
            'filter[instrument-id][condition][condition]': '=',
            'filter[instrument-id][condition][value]': pac_inst_id
        }
    )
    assert resp.status_code == 200
    return resp.json()['data'][0]['id']


def _create_file(session, file_obj):
    resp = session.post(
        '{}/node/pacifica_files'.format(get_config().get('drupal', 'url')),
        data=json.dumps({
            'data': {
                'type': 'node--pacifica_files',
                'attributes': {
                    'title': file_obj['name'],
                    'field_pac_file_id': file_obj['_id'],
                    'field_pac_file_checksum': '{}:{}'.format(file_obj['hashtype'], file_obj['hashsum']),
                    'field_pac_file_ctime': parser.parse(file_obj['ctime']).replace(microsecond=0).isoformat('T'),
                    'field_pac_file_mtime': parser.parse(file_obj['mtime']).replace(microsecond=0).isoformat('T'),
                    'field_pac_file_size': file_obj['size'],
                    'field_pac_file_subdir': file_obj['subdir']
                }
            }
        }),
        headers={
            'Content-Type': 'application/vnd.api+json'
        }
    )
    assert resp.status_code == 201
    return resp.json()['data']['id']


def _create_data_upload(session, *file_uuids, **meta):
    resp = session.post(
        '{}/node/pacifica_data_upload'.format(get_config().get('drupal', 'url')),
        data=json.dumps({
            'data': {
                'type': 'node--pacifica_data_upload',
                'attributes': {
                    'title': 'Transaction {}'.format(meta['trans_id']),
                    'field_pac_transaction_id': meta['trans_id']
                },
                'relationships': {
                    'field_pac_person': {
                        'data': [
                            {
                                'type': 'node--pacifica_person',
                                'id': meta['user_uuid']
                            }
                        ]
                    },
                    'field_pac_project': {
                        'data': [
                            {
                                'type': 'node--pacifica_project',
                                'id': meta['proj_uuid']
                            }
                        ]
                    },
                    'field_pac_data_source': {
                        'data': [
                            {
                                'type': 'node--pacifica_data_source',
                                'id': meta['inst_uuid']
                            }
                        ]
                    },
                    'field_pac_files': {
                        'data': [
                            {
                                'type': 'node--pacifica_files',
                                'id': file_uuid
                            }
                            for file_uuid in file_uuids
                        ]
                    }
                }
            }
        }),
        headers={
            'Content-Type': 'application/vnd.api+json'
        }
    )
    assert resp.status_code == 201
    return resp.json()['data']['id']


def _parse_metadata(meta):
    ret = {
        'proj_id': None,
        'user_id': None,
        'inst_id': None,
        'trans_id': None,
        'files': []
    }
    for obj in meta:
        if obj['destinationTable'] == 'Transactions._id':
            ret['trans_id'] = obj['value']
        elif obj['destinationTable'] == 'Transactions.submitter':
            ret['user_id'] = obj['value']
        elif obj['destinationTable'] == 'Transactions.project':
            ret['proj_id'] = obj['value']
        elif obj['destinationTable'] == 'Transactions.instrument':
            ret['inst_id'] = obj['value']
        elif obj['destinationTable'] == 'Files':
            ret['files'].append(obj)
    return ret


def post_metadata_drupal(meta):
    """Post metadata to drupal."""
    try:
        session = requests.session()
        # this really needs to be deligated from the rest auth somehow
        session.auth = ('bob', 'smith')
        parsed_meta = _parse_metadata(meta)
        user_uuid = _get_user_uuid(session, parsed_meta['user_id'])
        proj_uuid = _get_project_uuid(session, parsed_meta['proj_id'])
        inst_uuid = _get_instrument_uuid(session, parsed_meta['inst_id'])
        file_uuids = []
        for file_obj in parsed_meta['files']:
            file_uuids.append(_create_file(session, file_obj))
        _create_data_upload(
            session,
            *file_uuids,
            trans_id=parsed_meta['trans_id'],
            user_uuid=user_uuid,
            proj_uuid=proj_uuid,
            inst_uuid=inst_uuid
        )
    except requests.RequestException as ex:
        return (False, ex)
    return (True, None)
