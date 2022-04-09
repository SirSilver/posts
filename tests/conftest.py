"""Pytest fixtures."""


import dataclasses
from typing import Optional
import fastapi

import httpx
import pytest

import web


@dataclasses.dataclass
class StubUsersRegistry:
    """Stub implementatino of users registry for testing."""

    signup_calls: list[dict] = dataclasses.field(default_factory=list)

    def signup(self, req: web.SignupRequest):
        """Signup new user.

        Args:
            req: new signup user request.
        """
        self.signup_calls.append(req.dict())


@dataclasses.dataclass
class StubPostsCatalog:
    """Stub implementation of posts catalog for testing."""

    post_calls: list[dict] = dataclasses.field(default_factory=list)
    _posts: dict[web.PostID, dict] = dataclasses.field(default_factory=dict)

    def make_post(self, req: web.PostRequest) -> web.PostID:
        """Make a new post.

        Args:
            req: new post request.
        Returns:
            New post ID.
        """
        self.post_calls.append(req.dict())
        return len(self.post_calls)

    def add_post(self, post: dict):
        """Add post to catalog.

        This is helper func for tests setup.

        Args:
            post: will be added to catalog by its ID.
        """
        self._posts[post["id"]] = post

    def get(self, post_id: web.PostID) -> Optional[dict]:
        """Get post from catalog.

        Args:
            post_id: unique ID to look for.
        Returns:
            Saved post in catalog if found.
        """
        return self._posts.get(post_id)


@pytest.fixture()
def app(registry: StubUsersRegistry, catalog: StubPostsCatalog) -> fastapi.FastAPI:
    app_ = web.create_app()
    app_.dependency_overrides.update({web.registry: lambda: registry, web.catalog: lambda: catalog})
    return app_


@pytest.fixture()
def client(app: fastapi.FastAPI) -> httpx.AsyncClient:
    return httpx.AsyncClient(app=app, base_url="https://testserver")


@pytest.fixture()
def registry() -> StubUsersRegistry:
    return StubUsersRegistry()


@pytest.fixture()
def catalog() -> StubPostsCatalog:
    return StubPostsCatalog()
