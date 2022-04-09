"""Pytest fixtures."""


import dataclasses
from typing import Optional
import fastapi

import faker
import httpx
import pytest

import posts
import web


fake = faker.Faker()


@dataclasses.dataclass
class StubUsersRegistry:
    """Stub implementatino of users registry for testing."""

    signup_calls: list[tuple[str, str]] = dataclasses.field(default_factory=list)
    _users: dict[tuple, str] = dataclasses.field(default_factory=dict)

    def signup(self, username: str, password: str):
        """Signup new user.

        Args:
            username: user login identificator.
            password: user auth password.
        """
        self.signup_calls.append((username, password))

    def add_user(self, user: dict) -> str:
        """Add user to registry.

        This is helper func for tests setup.

        Args:
            user: will be added to registry.
        Returns:
            Assigned to user auth token.
        """
        token = fake.pystr()
        self._users[(user["username"], user["password"])] = token
        return token

    def login(self, username: str, password: str) -> str:
        """Login registered user.

        Args:
            username: user login identificator.
            password: user password to match with the one in registry.
        Returns:
            Access auth token.
        """
        return self._users[(username, password)]

    def add_token(self, token: str) -> str:
        """Add token to registry.

        This is helper func for tests setup.

        Args:
            token: auth token
        Returns:
            Assigned to this token username.
        """
        username, password = fake.pystr(), fake.pystr()
        self._users[(username, password)] = token
        return username

    def authenticate(self, token: str) -> dict | None:
        """Authenticate user with a token.

        Args:
            token: auth token given on user login.
        Returns:
            Aunthenticated user.
        """
        try:
            user, _ = next(u for u in self._users if self._users[u] == token)
        except StopIteration:
            return None

        return user


@dataclasses.dataclass
class StubPostsCatalog:
    """Stub implementation of posts catalog for testing."""

    post_calls: list[tuple[str, dict]] = dataclasses.field(default_factory=list)
    _posts: dict[posts.ID, dict] = dataclasses.field(default_factory=dict)

    def make_post(self, author: str, req: posts.MakePostRequest) -> posts.ID:
        """Make a new post.

        Args:
            author: user making new post.
            req: new post request.
        Returns:
            New post ID.
        """
        self.post_calls.append((author, req.dict()))
        return len(self.post_calls)

    def add_post(self, post: dict):
        """Add post to catalog.

        This is helper func for tests setup.

        Args:
            post: will be added to catalog by its ID.
        """
        self._posts[post["id"]] = post

    def get(self, post_id: posts.ID) -> Optional[dict]:
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
