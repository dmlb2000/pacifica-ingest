#!/usr/bin/python
"""This module pushes the metadata to Drupal's JSON:API endpoints."""
from json import dumps, loads
from itertools import accumulate
import requests
from sqlalchemy.orm import Session as SQLSession
from .abstract import MetaXFerBase
from ..orm import Session

class MetaXFerDrupalJSONAPI(MetaXFerBase):
    """Metadata transfer to Drupal's JSON:API endpoint."""

    def _merge_headers(self, add_headers=None):
        """Merge the configparser headers with additional headers passed."""
        ret = {}
        ret.update({ key: value for key,value in self.configparser.items('drupal_headers') })
        ret.update(add_headers if add_headers else {})
        return ret

    def _load_jsonapi(self, jsondata):
        resp = requests.post(
            "{}/node/{}".format(
                self.configparser.get('drupal', 'url'),
                self.configparser.get('drupal', 'content_type')
            ),
            json=jsondata,
            headers=self._merge_headers({
                'Accept': 'application/vnd.api+json',
                'Content-Type': 'application/vnd.api+json',
            })
        )
        assert resp.status_code == 201


    def upload(self, _db: SQLSession, session: Session, filemeta: dict) -> None:
        """Upload the metadata from the session and files."""
        resp = requests.get(
            "{}/user/user".format(self.configparser.get('drupal', 'url')),
            headers=self._merge_headers({
                'Accept': 'application/vnd.api+json'
            }),
        )
        author_obj = {}
        display_name = self.configparser.get('drupal', 'content_author')
        for user_obj in resp.json().get('data', []):
            if user_obj.get('attributes', {}).get('display_name', None) == display_name:
                author_obj = user_obj
        if not author_obj:
            raise RuntimeError('No Drupal user with display name {}'.format(display_name))

        self._load_jsonapi({
            "data": {
                "type": "node--{}".format(self.configparser.get('drupal', 'content_type').replace('_', '-')),
                "attributes": {
                    "title": session.name,
                    "field_pacifica_size": accumulate([x.filesize for x in filemeta]),
                    "field_file_data": {
                        "value": dumps(filemeta)
                    }
                },
                "relationships": {
                    "uid": {
                        "data": {
                            "type": "user--user",
                            "id": author_obj.get('id', '')
                        }
                    }
                }
            }
        })
        if session.metadata_doc:
            self._load_jsonapi(
                loads(session.metadata_doc)
            )
