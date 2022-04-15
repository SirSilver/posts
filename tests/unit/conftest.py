"""Pytest fixtures for unit tests suite."""


from typing import Generator

import pytest
import sqlalchemy as sa

import tables


@pytest.fixture()
def engine() -> Generator[sa.engine.Engine, None, None]:
    engine_ = sa.create_engine("sqlite+pysqlite:///:memory:", future=True)
    tables.metadata.create_all(engine_)
    yield engine_
    tables.metadata.drop_all(engine_)
