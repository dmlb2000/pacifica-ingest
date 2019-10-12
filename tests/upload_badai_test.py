#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Test ingest with a disabled archive interface."""
from __future__ import print_function, absolute_import
from .common_methods_test import try_good_upload, try_good_move


# this is a long name but descriptive.
# pylint: disable=invalid-name
def test_bad_archiveinterface_upload():
    """Test if the archive interface is down."""
    try_good_upload('good', 'FAILED', 'ingest files', 0, 10)
# pylint: enable=invalid-name


def test_bad_ai_move():
    """Test the good move."""
    try_good_move('move-md', 'FAILED', 'move files', 0, 10)
