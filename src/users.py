"""Users module."""


import datetime
import hashlib
import os

from jose import jwt
import sqlalchemy as sa
from sqlalchemy import exc
from sqlalchemy.engine import base

import tables


SECRET_KEY = os.getenv("SECRET_KEY", "b95b59f177585138466f60dcade5c26b1710b3714ce1c9d1613af584c4591b8a")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_LIFETIME = 2 * 60


class UserExists(Exception):
    """User with given username already exists."""


class Unauthorized(Exception):
    """User is unauthorized."""


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
        password_hash = _hash_password(password, salt)
        insert = tables.users.insert().values(username=username, password=password_hash, salt=salt)
        try:
            self._connection.execute(insert)
        except exc.IntegrityError:
            raise UserExists

    def login(self, username: str, password: str) -> str:
        """Login registered user.

        Args:
            username: user login identificator.
            password: user password to match with the one in registry.
        Returns:
            Access auth JWT token.
        """
        columns = (tables.users.c.username, tables.users.c.password, tables.users.c.salt)
        select = sa.select(*columns).where(tables.users.c.username == username)
        result = self._connection.execute(select).fetchone()

        if not result:
            raise Unauthorized

        username, password_hash, salt = result

        if password_hash != _hash_password(password, salt):
            raise Unauthorized

        expires = datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_LIFETIME)
        update = sa.update(tables.users).where(tables.users.c.username == username).values(last_login=sa.func.now())
        self._connection.execute(update)

        return jwt.encode({"sub": username, "exp": expires}, SECRET_KEY, JWT_ALGORITHM)

    def authenticate(self, token: str) -> str:
        """Authenticate user with a token.

        Args:
            token: auth token given on user login.
        Returns:
            Aunthenticated user name.
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, JWT_ALGORITHM)
        except jwt.JWTError:
            raise Unauthorized

        try:
            username = payload["sub"]
        except KeyError:
            raise Unauthorized

        select = tables.users.select().where(tables.users.c.username == username)
        result = self._connection.execute(select).fetchone()

        if not result:
            raise Unauthorized

        return username

    def track_activity(self, username: str):
        """Track user activity.

        Args:
            username: user login identificator.
        """
        now = datetime.datetime.utcnow()
        insert = tables.users.update().where(tables.users.c.username == username).values(last_activity=now)
        self._connection.execute(insert)

    def get_activities(self, username: str) -> tuple[datetime.datetime, datetime.datetime]:
        """Get last user actities tracks.

        Args:
            username: user login identificator.
        Returns:
            Last login and last activity datetime.
        """
        select = sa.select(tables.users.c.last_login, tables.users.c.last_activity).where(
            tables.users.c.username == username
        )
        result = self._connection.execute(select).fetchone()
        assert result is not None

        return result.last_login, result.last_activity


def _hash_password(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000, 128)
