from __future__ import annotations

from typing import TYPE_CHECKING

import faker
import httpx

if TYPE_CHECKING:
    from tests.conftest import StubPostsCatalog, StubUsersRegistry
    import posts

fake = faker.Faker()


class TestPOSTSignup:
    """Test users signup."""

    async def test_registering_user(self, client: httpx.AsyncClient, registry: StubUsersRegistry):
        request = _random_signup_request()

        resp = await _signup(client, request)

        _assert_code(resp, httpx.codes.CREATED)
        _assert_body(resp, {"links": [{"rel": "login", "href": "/login", "action": "POST"}]})
        _assert_registered(registry, request)


class TestPOSTLogin:
    """Tests user login."""

    async def test_login_user(self, client: httpx.AsyncClient, registry: StubUsersRegistry):
        user = _random_user()
        token = registry.add_user(user)
        request = _new_login_request(user)

        resp = await _login(client, request)

        _assert_code(resp, httpx.codes.OK)
        _assert_body(resp, {"token": token})


class TestPOSTPosts:
    """Test posts resource POST endpoint."""

    async def test_creating_post(
        self, client: httpx.AsyncClient, catalog: StubPostsCatalog, registry: StubUsersRegistry
    ):
        request = _random_post_request()
        username = _authorize(client, registry)

        resp = await _make_post(client, request)

        _assert_code(resp, httpx.codes.CREATED)
        _assert_location(resp, "/posts/1")
        _assert_posted(catalog, username, request)

    async def test_without_authorization(self, client: httpx.AsyncClient):
        request = _random_post_request()

        resp = await _make_post(client, request)

        _assert_code(resp, httpx.codes.UNAUTHORIZED)
        _assert_body(resp, {"detail": "Unauthorized"})

    async def test_with_incorrect_auth(self, client: httpx.AsyncClient):
        request = _random_post_request()
        client.headers["Authorization"] = "Bearer invalid_token"

        resp = await _make_post(client, request)

        _assert_code(resp, httpx.codes.FORBIDDEN)
        _assert_body(resp, {"detail": "Forbidden"})


class TestGETPost:
    """Test post resource GET endpoint."""

    async def test_retrieving_post(self, client: httpx.AsyncClient, catalog: StubPostsCatalog):
        post = _random_post()
        catalog.add_post(post)

        resp = await _get_post(client, post["id"])

        _assert_code(resp, httpx.codes.OK)
        _assert_body(resp, post | {"links": []})

    async def test_with_non_existent_post(self, client: httpx.AsyncClient):
        resp = await _get_post(client, fake.pyint(min_value=1))

        _assert_code(resp, httpx.codes.NOT_FOUND)
        _assert_body(resp, {"detail": "Not Found"})

    async def test_retrieving_as_post_author(
        self, client: httpx.AsyncClient, catalog: StubPostsCatalog, registry: StubUsersRegistry
    ):
        username = _authorize(client, registry)
        post = _random_post(username)
        catalog.add_post(post)

        resp = await _get_post(client, post["id"])

        _assert_code(resp, httpx.codes.OK)
        _assert_body(resp, post | {"links": []})

    async def test_with_user_already_liked_the_post(
        self, client: httpx.AsyncClient, catalog: StubPostsCatalog, registry: StubUsersRegistry
    ):
        post = _random_post()
        catalog.add_post(post)
        username = _authorize(client, registry)
        catalog.add_like(username, post["id"])

        resp = await _get_post(client, post["id"])

        _assert_code(resp, httpx.codes.OK)
        want_links = [{"rel": "unlike", "href": f"/posts/{post['id']}/likes", "action": "DELETE"}]
        _assert_body(resp, post | {"links": want_links})


class TestPOSTLikes:
    """Test post resource POST like endpoint."""

    async def test_liking_post(self, client: httpx.AsyncClient, catalog: StubPostsCatalog, registry: StubUsersRegistry):
        post = _random_post()
        catalog.add_post(post)
        username = _authorize(client, registry)

        resp = await _like_post(client, post["id"])

        _assert_code(resp, httpx.codes.OK)
        _assert_body(resp, {"links": [{"rel": "unlike", "href": f"/posts/{post['id']}/likes", "action": "DELETE"}]})
        _assert_liked(catalog, post["id"], username)

    async def test_with_unauth_user(self, client: httpx.AsyncClient, catalog: StubPostsCatalog):
        post = _random_post()
        catalog.add_post(post)

        resp = await _like_post(client, post["id"])

        _assert_code(resp, httpx.codes.UNAUTHORIZED)
        _assert_no_likes(catalog)

    async def test_with_already_liked_user(
        self, client: httpx.AsyncClient, catalog: StubPostsCatalog, registry: StubUsersRegistry
    ):
        post = _random_post()
        catalog.add_post(post)
        username = _authorize(client, registry)
        catalog.add_like(username, post["id"])

        resp = await _like_post(client, post["id"])

        _assert_code(resp, httpx.codes.FORBIDDEN)
        _assert_body(resp, {"detail": "You already liked this post"})
        _assert_no_likes(catalog)


def _random_signup_request() -> dict:
    return {"username": fake.pystr(), "password": fake.pystr()}


def _new_login_request(user: dict) -> dict:
    return {"username": user["username"], "password": user["password"]}


def _random_post_request() -> dict:
    return {"title": fake.pystr(), "description": fake.pystr()}


def _random_user() -> dict:
    return {"username": fake.pystr(), "password": fake.pystr()}


def _random_post(author: str | None = None) -> dict:
    if author is None:
        author = fake.pystr()

    return {"id": fake.pyint(min_value=1), "author": author} | _random_post_request()


def _authorize(client: httpx.AsyncClient, registry: StubUsersRegistry) -> str:
    token = fake.pystr()
    username = registry.add_token(token)

    client.headers["Authorization"] = f"Bearer {token}"
    return username


async def _signup(client: httpx.AsyncClient, request: dict) -> httpx.Response:
    return await client.post("/users", json=request)


async def _login(client: httpx.AsyncClient, request: dict) -> httpx.Response:
    return await client.post("/users/login", json=request)


async def _make_post(client: httpx.AsyncClient, post: dict) -> httpx.Response:
    return await client.post("/posts", json=post)


async def _get_post(client: httpx.AsyncClient, post_id: posts.ID) -> httpx.Response:
    return await client.get(f"/posts/{post_id}")


async def _like_post(client: httpx.AsyncClient, post_id: posts.ID) -> httpx.Response:
    return await client.post(f"/posts/{post_id}/likes")


def _assert_code(resp: httpx.Response, want: int):
    have = resp.status_code
    assert have == want, f"Invalid status code received\nhave {have}\nwant {want}"


def _assert_registered(registry: StubUsersRegistry, request: dict):
    assert len(registry.signup_calls) == 1, f"Have {len(registry.signup_calls)} calls to signup, want 1"
    err = f"Didn't signup correct user, have {registry.signup_calls[0]}, want {request}"
    assert registry.signup_calls[0] == (request["username"], request["password"]), err


def _assert_location(resp: httpx.Response, want: str):
    assert "location" in resp.headers, "Missing location header"
    have = resp.headers["location"]
    assert have == want, f"Invalid location received\nhave {have}\nwant {want}"


def _assert_posted(catalog: StubPostsCatalog, username: str, post: dict):
    assert len(catalog.post_calls) == 1, f"Have {len(catalog.post_calls)} calls to post, want 1"
    err = f"Have {catalog.post_calls[0]} args to post call, want ({username}, {post})"
    assert catalog.post_calls[0] == (username, post), err


def _assert_body(resp: httpx.Response, body: dict):
    assert resp.json() == body, f"Didn't get correct response, have {resp.json()}, want {body}"


def _assert_liked(catalog: StubPostsCatalog, post_id: posts.ID, username: str):
    assert len(catalog.likes_calls) == 1, f"Have {len(catalog.likes_calls)} calls to like, want 1"
    err = f"Have {catalog.likes_calls[0]} args to like call, want ({post_id}, {username})"
    assert catalog.likes_calls[0] == (post_id, username), err


def _assert_no_likes(catalog: StubPostsCatalog):
    assert not catalog.likes_calls, "Catalog has likes"
