#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Utilities Module."""
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


@contextmanager
def get_db_session(configparser):
    """Context to create sqlalchemy engine."""
    engine = create_engine(configparser.get('database', 'db_url'), echo=False)
    session = scoped_session(sessionmaker(autoflush=True, autocommit=False))
    session.configure(bind=engine)
    try:
        yield session
    finally:
        try:
            # pylint: disable=no-member
            session.commit()
        except Exception as ex:
            # pylint: disable=no-member
            session.rollback()
            raise Exception from ex
        finally:
            session.remove()
