#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Test script to run the command interface for testing."""
import sys
from pacifica.ingest.__main__ import cmd

if __name__ == '__main__':
    sys.exit(cmd())
