#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Celery Application Module."""
from celery import Celery
from .settings import celery_settings

app = Celery('ingest')
app.conf.update(**celery_settings)
