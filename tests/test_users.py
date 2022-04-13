import hashlib

import faker
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
