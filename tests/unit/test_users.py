import datetime
import hashlib
import os
from typing import Optional

import faker
from jose import jwt
import pytest
import sqlalchemy
from sqlalchemy.engine import base

import tables
import users


engine = sqlalchemy.create_engine("sqlite+pysqlite:///:memory:", future=True)
tables.metadata.create_all(engine)
fake = faker.Faker()


class TestSignup:
    def test_register_user(self):
        with engine.begin() as connection:
            registry = users.Registry(connection)
            username, password = fake.pystr(), fake.pystr()

            registry.signup(username, password)

            _assert_registered(connection, username, password)

    def test_with_existing_username(self):
        with engine.begin() as connection:
            registry = users.Registry(connection)
            username, password = fake.pystr(), fake.pystr()

            registry.signup(username, password)

            with pytest.raises(users.UserExists):
                registry.signup(username, password)


class TestLogin:
    def test_signing_in_user(self):
        with engine.begin() as connection:
            registry = users.Registry(connection)
            username, password = fake.pystr(), fake.pystr()
            _insert_user(connection, username, password)

            token = registry.login(username, password)

            _assert_token(token, username)
            _assert_login_tracked(connection, username)

    def test_with_wrong_password(self):
        with engine.begin() as connection:
            registry = users.Registry(connection)
            username, password = fake.pystr(), fake.pystr()
            _insert_user(connection, username, password)

            with pytest.raises(users.Unauthorized):
                registry.login(username, fake.pystr())

    def test_with_non_existent_user(self):
        with engine.begin() as connection:
            registry = users.Registry(connection)
            username, password = fake.pystr(), fake.pystr()

            with pytest.raises(users.Unauthorized):
                registry.login(username, password)


class TestAuthenticate:
    def test_returns_username(self):
        with engine.begin() as connection:
            registry = users.Registry(connection)
            username, password = fake.pystr(), fake.pystr()
            _insert_user(connection, username, password)
            token = _encode_token(username)

            have = registry.authenticate(token)

            assert have == username, "Got wrong username from token"

    def test_with_wrong_token_claims(self):
        with engine.begin() as connection:
            registry = users.Registry(connection)
            username, password = fake.pystr(), fake.pystr()
            _insert_user(connection, username, password)
            token = jwt.encode({"invalid": "invalid"}, users.SECRET_KEY, users.JWT_ALGORITHM)

            with pytest.raises(users.Unauthorized):
                registry.authenticate(token)

    def test_with_non_existent_user(self):
        with engine.begin() as connection:
            registry = users.Registry(connection)
            username = fake.pystr()
            token = _encode_token(username)

            with pytest.raises(users.Unauthorized):
                registry.authenticate(token)

    def test_with_invalid_token(self):
        with engine.begin() as connection:
            registry = users.Registry(connection)
            username, password = fake.pystr(), fake.pystr()
            _insert_user(connection, username, password)
            token = fake.pystr()

            with pytest.raises(users.Unauthorized):
                registry.authenticate(token)

    def test_with_expired_token(self):
        with engine.begin() as connection:
            registry = users.Registry(connection)
            username, password = fake.pystr(), fake.pystr()
            _insert_user(connection, username, password)
            expires = datetime.datetime.utcnow() - datetime.timedelta(seconds=1)
            token = _encode_token(username, expires)

            with pytest.raises(users.Unauthorized):
                registry.authenticate(token)


class TestTrackActivity:
    def test_records_activity_time(self):
        with engine.begin() as connection:
            registry = users.Registry(connection)
            username, password = fake.pystr(), fake.pystr()
            _insert_user(connection, username, password)

            registry.track_activity(username)

            _assert_tracked(connection, username)


class TestGetActivities:
    def test_returns_last_login_and_last_activity(self):
        with engine.begin() as connection:
            registry = users.Registry(connection)
            username, password = fake.pystr(), fake.pystr()
            last_login, last_activity = fake.date_time(), fake.date_time()
            _insert_user(connection, username, password)
            _update_tracks(connection, username, last_login, last_activity)

            login, activity = registry.get_activities(username)

            assert login == last_login, "Wrong last login returned"
            assert activity == last_activity, "Wrong last activity returned"


def _insert_user(connection: base.Connection, username: str, password: str):
    salt = os.urandom(32)
    password_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000, 128)
    text = "INSERT INTO users (username, password, salt) VALUES (:username, :password, :salt)"
    insert = sqlalchemy.text(text).bindparams(username=username, password=password_hash, salt=salt)
    connection.execute(insert)


def _update_tracks(connection: base.Connection, username: str, last_login: datetime.datetime, last_activity: datetime.datetime):
    text = "UPDATE users SET last_login = :last_login, last_activity = :last_activity WHERE users.username = :username"
    update = sqlalchemy.text(text).bindparams(last_login=last_login, last_activity=last_activity, username=username)
    connection.execute(update)


def _encode_token(username: str, expires: Optional[datetime.datetime] = None):
    if expires is None:
        expires = datetime.datetime.utcnow() + datetime.timedelta(minutes=users.ACCESS_TOKEN_LIFETIME)

    return jwt.encode({"sub": username, "exp": expires}, users.SECRET_KEY, users.JWT_ALGORITHM)


def _assert_registered(connection: base.Connection, username: str, password: str):
    text = "SELECT username, password, salt FROM users WHERE users.username == :username"
    select = sqlalchemy.text(text).bindparams(username=username)
    result = connection.execute(select).fetchone()
    assert result is not None, "User has not been registered"
    username, password_hash, salt = result
    assert username == username, "Wrong username saved"
    assert password_hash == hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt, 100_000, 128
    ), "Wrong password hash saved"


def _assert_token(token: str, username: str):
    payload = jwt.decode(token, users.SECRET_KEY, users.JWT_ALGORITHM)

    assert payload["sub"] == username, "Token does not contain expected username"

    have_expire = datetime.datetime.utcfromtimestamp(payload["exp"])

    now = datetime.datetime.utcnow()
    delta = datetime.timedelta(minutes=users.ACCESS_TOKEN_LIFETIME)
    want_expire = (now + delta).replace(microsecond=0)

    assert have_expire == want_expire, "Token has wrong expire time"


def _assert_login_tracked(connection: base.Connection, username: str):
    text = "SELECT last_login FROM users WHERE users.username == :username"
    select = sqlalchemy.text(text).bindparams(username=username)
    result = connection.execute(select).fetchone()

    assert result is not None
    assert result.last_login is not None
    have = datetime.datetime.fromisoformat(result.last_login).replace(microsecond=0)
    assert have == datetime.datetime.utcnow().replace(microsecond=0), "Wrong datetime tracked"


def _assert_tracked(connection: base.Connection, username: str):
    text = "SELECT last_activity FROM users WHERE users.username == :username"
    select = sqlalchemy.text(text).bindparams(username=username)
    result = connection.execute(select).fetchone()

    assert result is not None, "Activity has not been tracked"
    have = datetime.datetime.fromisoformat(result.last_activity).replace(microsecond=0)
    assert have == datetime.datetime.utcnow().replace(microsecond=0), "Wrong datetime tracked"
