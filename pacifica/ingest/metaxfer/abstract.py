#!/usr/bin/python
"""Abstract class for metadata transfer."""
from configparser import ConfigParser
import abc
from sqlalchemy.orm import Session as SQLSession
from ..orm import Session


class MetaXFerBase(abc.ABC):
    """
    Interface class for metadata uploads.
    
    This class defines the interface for metadata to be transformed
    and/or uploaded to something.
    """

    def __init__(self, configparser: ConfigParser):
        """Create the object by trying to find the config parser."""
        self.configparser = configparser

    @abc.abstractmethod
    def upload(self, db: SQLSession, session: Session, filemeta: dict) -> None:
        """Upload the metadata from the session and files."""