#!/usr/bin/python
"""Abstract base class for backends."""
import abc
from ..orm import Session


class FileXFerBase(abc.ABC):
    """Base class for file transfer interface."""

    @abc.abstractmethod
    def generate_user_auth(self, session: Session) -> None:
        """
        Generate User Authentication.

        Create a user authentication for the session and store
        the result in the `user_auth` field of the session.
        The `user_auth` field must be json_serializable.
        """

    @abc.abstractmethod
    def create_session(self, session: Session) -> None:
        """
        Create the session state.

        This creates the local session state required to setup
        the backend service to allow access to the user created
        in `generate_user_auth()`. This may involve creating
        local directories, adding the user with the password,
        manipulating permissions, etc.
        """

    @abc.abstractmethod
    def delete_session(self, session: Session) -> None:
        """
        Delete the session and local state.

        This deletes the local session and everything else you
        did in `create_session()`.
        """
