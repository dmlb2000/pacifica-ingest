#!/usr/bin/python
# -*- coding: utf-8 -*-
"""ORM for index server."""
from time import sleep
from datetime import datetime
from peewee import Model, OperationalError, BooleanField
from peewee import CharField, IntegerField, BigIntegerField, TextField, DateTimeField, DecimalField
from playhouse.migrate import SchemaMigrator, migrate
from playhouse.db_url import connect
from pacifica.ingest.config import get_config

SCHEMA_MAJOR = 2
SCHEMA_MINOR = 0
DB = connect(get_config().get('database', 'peewee_url'))


class OrmSync(object):
    """
    Special module for syncing the orm.

    This module should incorporate a schema migration strategy.

    The supported versions migrating forward must be in a versions array
    containing tuples for major and minor versions.

    The version tuples are directly translated to method names in the
    orm_update class for the update between those versions.

    Example Version Control::

      class orm_update:
        versions = [
          (0, 1),
          (0, 2),
          (1, 0),
          (1, 1)
        ]

        def update_0_1_to_0_2():
            pass
        def update_0_2_to_1_0():
            pass

    The body of the update should follow peewee migration practices.
    http://docs.peewee-orm.com/en/latest/peewee/playhouse.html#migrate
    """

    versions = [
        (0, 0),
        (1, 0),
        (2, 0)
    ]

    @staticmethod
    def dbconn_blocking():
        """Wait for the db connection."""
        dbcon_attempts = get_config().getint('database', 'connect_attempts')
        dbcon_wait = get_config().getint('database', 'connect_wait')
        while dbcon_attempts:
            try:
                IngestState.database_connect()
                return
            except OperationalError:
                # couldnt connect, potentially wait and try again
                sleep(dbcon_wait)
                dbcon_attempts -= 1
        raise OperationalError('Failed database connect retry.')

    @classmethod
    def update_0_0_to_1_0(cls):
        """Update by creating the table."""
        if not IngestState.table_exists():
            IngestState.create_table()
        col_names = [col_md.name for col_md in DB.get_columns('ingeststate')]
        if 'complete' in col_names:
            migrator = SchemaMigrator(DB)
            migrate(migrator.drop_column(
                'ingeststate', 'complete'
            ))

    @classmethod
    def update_1_0_to_2_0(cls):
        """Update by adding the boolean column."""
        migrator = SchemaMigrator(DB)
        migrate(migrator.add_column(
            'ingeststate', 'complete',
            BooleanField(default=False)
        ))

    @classmethod
    def update_tables(cls):
        """Update the database to the current version."""
        verlist = cls.versions
        db_ver = IngestStateSystem.get_version()
        if verlist.index(verlist[-1]) == verlist.index(db_ver):
            # we have the current version don't update
            return True
        with IngestState.atomic():
            for db_ver in verlist[verlist.index(db_ver):-1]:
                next_db_ver = verlist[verlist.index(db_ver)+1]
                method_name = 'update_{}_to_{}'.format(
                    '{}_{}'.format(*db_ver),
                    '{}_{}'.format(*next_db_ver)
                )
                getattr(cls, method_name)()
            IngestStateSystem.drop_table()
            IngestStateSystem.create_table()
            IngestStateSystem.get_or_create_version()
        return True


# pylint: disable=too-few-public-methods
class BaseModel(Model):
    """Auto-generated by pwiz."""

    class Meta(object):
        """Map to the database connected above."""

        database = DB


class IngestStateSystem(BaseModel):
    """Ingest State Schema Version Model."""

    part = CharField(primary_key=True)
    value = IntegerField(default=-1)

    @classmethod
    def get_or_create_version(cls):
        """Set or create the current version of the schema."""
        if not cls.table_exists():
            return (0, 0)
        major, _created = cls.get_or_create(part='major', value=SCHEMA_MAJOR)
        minor, _created = cls.get_or_create(part='minor', value=SCHEMA_MINOR)
        return (major, minor)

    @classmethod
    def get_version(cls):
        """Get the current version as a tuple."""
        if not cls.table_exists():
            return (0, 0)
        return (cls.get(part='major').value, cls.get(part='minor').value)

    @classmethod
    def is_equal(cls):
        """Check to see if schema version matches code version."""
        major, minor = cls.get_version()
        return major == SCHEMA_MAJOR and minor == SCHEMA_MINOR

    @classmethod
    def is_safe(cls):
        """Check to see if the schema version is safe for the code."""
        major, _minor = cls.get_version()
        return major == SCHEMA_MAJOR


class IngestState(BaseModel):
    """Map a python record to a mysql table."""

    job_id = BigIntegerField(primary_key=True, column_name='id')
    state = CharField()
    task = CharField()
    task_percent = DecimalField()
    exception = TextField(default='')
    complete = BooleanField(default=False)
    created = DateTimeField(default=datetime.utcnow)
    updated = DateTimeField(default=datetime.utcnow)

    @classmethod
    def atomic(cls):
        """Get the atomic context or decorator."""
        # pylint: disable=no-member
        return cls._meta.database.atomic()
        # pylint: enable=no-member

    @classmethod
    def database_connect(cls):
        """
        Make sure database is connected.

        Trying to connect a second
        time *does* cause problems.
        """
        # pylint: disable=no-member
        if not cls._meta.database.is_closed():
            cls._meta.database.close()
        cls._meta.database.connect()
        # pylint: enable=no-member

    @classmethod
    def database_close(cls):
        """
        Close the database connection.

        Closing already closed database
        is not a problem, so continue on.
        """
        # pylint: disable=no-member
        if not cls._meta.database.is_closed():
            cls._meta.database.close()
        # pylint: enable=no-member

    class Meta(object):
        """Map to uniqueindex table."""

        table_name = 'ingeststate'
# pylint: enable=too-few-public-methods


def update_state(job_id, state, task, task_percent, exception=''):
    """Update the state of an ingest job."""
    completed = False
    if state == 'FAILED' or (task == 'ingest metadata' and task_percent == 100):
        completed = True
    if job_id and int(job_id) >= 0:
        IngestState.database_connect()
        record = IngestState.get_or_create(job_id=job_id,
                                           defaults={'task': '', 'task_percent': 0, 'state': ''})[0]

        record.state = state
        record.task = task
        record.task_percent = task_percent
        record.exception = exception
        record.complete = completed
        record.updated = datetime.utcnow()
        record.save()
        IngestState.database_close()


def read_state(job_id):
    """Return the state of an ingest job as a json object."""
    IngestState.database_connect()
    if job_id and job_id >= 0:
        record = IngestState.get(job_id=job_id)
    else:
        record = IngestState()
        record.state = 'DATA_ACCESS_ERROR'
        record.task = 'read_state'
        record.task_percent = 0
    IngestState.database_close()
    return record
