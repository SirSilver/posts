"""Users module."""


import hashlib
import os
from sqlalchemy.engine import base

import tables


class Registry:
    """Users registry."""

    def __init__(self, connection: base.Connection):
        self._connection = connection

    def signup(self, username: str, password: str):
        """Signup new user.

        Saves password as hash with random salt.

        Args:
            username: user login identificator.
            password: user auth password.
        """
        salt = os.urandom(32)
        password_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000, 128)
        insert = tables.users.insert().values(username=username, password=password_hash, salt=salt)
        self._connection.execute(insert)

    def login(self, username: str, password: str) -> str:
        """Login registered user.

        Args:
            username: user login identificator.
            password: user password to match with the one in registry.
        Returns:
            Access auth token.
        """
        ...

    def authenticate(self, token: str) -> str:
        """Authenticate user with a token.

        Args:
            token: auth token given on user login.
        Returns:
            Aunthenticated user name.
        """
        ...

    def track_activity(self, username: str):
        """Track user activity.

        Args:
            username: user login identificator.
        """
        ...
