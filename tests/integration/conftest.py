"""Pytest fixtures."""


from typing import Generator
import fastapi
import httpx
import pytest
import sqlalchemy
from sqlalchemy.engine import base

import posts
import tables
import users
import web


@pytest.fixture()
def engine() -> Generator[sqlalchemy.engine.Engine, None, None]:
    engine = sqlalchemy.create_engine(
        "sqlite+pysqlite:///:memory:", future=True, connect_args={"check_same_thread": False}
    )
    tables.metadata.create_all(engine)
    yield engine
    tables.metadata.drop_all(engine)


@pytest.fixture()
def app(engine: sqlalchemy.engine.Engine) -> Generator[fastapi.FastAPI, None, None]:
    app_ = web.create_app()

    def catalog(connection: base.Connection) -> posts.Catalog:
        return posts.Catalog(connection)

    def registry(connection: base.Connection) -> users.Registry:
        return users.Registry(connection)

    with engine.begin() as connection:
        app_.dependency_overrides.update(
            {web.catalog: lambda: catalog(connection), web.registry: lambda: registry(connection)}
        )
        yield app_


@pytest.fixture()
def client(app: fastapi.FastAPI) -> httpx.AsyncClient:
    return httpx.AsyncClient(app=app, base_url="https://testserver")
