"""Pytest fixtures."""


import dataclasses
import fastapi

import httpx
import pytest

import web


@dataclasses.dataclass
class StubPostsCatalog:
    """Stub implementation of posts catalog for testing."""

    post_calls: list[dict] = dataclasses.field(default_factory=list)

    def make_post(self, req: web.PostRequest) -> web.PostID:
        """Make a new post."""
        self.post_calls.append(req.dict())
        return len(self.post_calls)


@pytest.fixture()
def app(catalog: StubPostsCatalog) -> fastapi.FastAPI:
    app_ = web.create_app()
    app_.dependency_overrides[web.catalog] = lambda: catalog
    return app_


@pytest.fixture()
def client(app: fastapi.FastAPI) -> httpx.AsyncClient:
    return httpx.AsyncClient(app=app, base_url="https://testserver")


@pytest.fixture()
def catalog() -> StubPostsCatalog:
    return StubPostsCatalog()
