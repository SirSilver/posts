from __future__ import annotations
import datetime

from typing import TYPE_CHECKING

import faker
import httpx

from web import users

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

    async def test_with_existing_user(self, client: httpx.AsyncClient, registry: StubUsersRegistry):
        request = _random_signup_request()
        registry.signup(request["username"], request["password"])

        resp = await _signup(client, request)

        _assert_code(resp, httpx.codes.BAD_REQUEST)
        _assert_body(resp, {"detail": users.USER_EXISTS_ERROR})


class TestPOSTLogin:
    """Tests user login."""

    async def test_login_user(self, client: httpx.AsyncClient, registry: StubUsersRegistry):
        user = _random_user()
        token = registry.add_user(user)
        request = _new_login_request(user)

        resp = await _login(client, request)

        _assert_code(resp, httpx.codes.OK)
        _assert_body(resp, {"access_token": token, "token_type": "bearer"})
        _assert_activity_tracked(registry, user["username"])

    async def test_with_wrong_token(self, client: httpx.AsyncClient):
        user = _random_user()
        client.headers["Authorization"] = f"Bearer {fake.pystr()}"
        request = _new_login_request(user)

        resp = await _login(client, request)

        _assert_code(resp, httpx.codes.UNAUTHORIZED)


class TestGETUserActivity:
    async def test_retrieving_user_activity(self, client: httpx.AsyncClient, registry: StubUsersRegistry):
        username = _authorize(client, registry)
        last_login, last_activity = fake.date_object(), fake.date_object()
        registry.add_tracks(username, last_login, last_activity)

        resp = await _get_activity(client)

        _assert_body(resp, {"last_login": last_login.isoformat(), "last_activity": last_activity.isoformat()})

    async def test_with_unauth_user(self, client: httpx.AsyncClient):
        resp = await _get_activity(client)

        _assert_code(resp, httpx.codes.UNAUTHORIZED)


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
        _assert_activity_tracked(registry, username)

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
        _assert_activity_tracked(registry, username)

    async def test_with_user_already_liked_the_post(
        self, client: httpx.AsyncClient, catalog: StubPostsCatalog, registry: StubUsersRegistry
    ):
        post = _random_post()
        catalog.add_post(post)
        username = _authorize(client, registry)
        catalog.add_like(username, post["id"])

        resp = await _get_post(client, post["id"])

        _assert_code(resp, httpx.codes.OK)
        want_links = [{"rel": "unlike", "href": f"/posts/{post['id']}/like", "action": "DELETE"}]
        _assert_body(resp, post | {"links": want_links})
        _assert_activity_tracked(registry, username)

    async def test_with_user_did_not_like_the_post(
        self, client: httpx.AsyncClient, catalog: StubPostsCatalog, registry: StubUsersRegistry
    ):
        post = _random_post()
        catalog.add_post(post)
        username = _authorize(client, registry)

        resp = await _get_post(client, post["id"])

        _assert_code(resp, httpx.codes.OK)
        _assert_body(resp, post | {"links": [{"rel": "like", "href": f"/posts/{post['id']}/like", "action": "POST"}]})
        _assert_activity_tracked(registry, username)


class TestPOSTLikes:
    """Test post resource POST like endpoint."""

    async def test_liking_post(self, client: httpx.AsyncClient, catalog: StubPostsCatalog, registry: StubUsersRegistry):
        post = _random_post()
        catalog.add_post(post)
        username = _authorize(client, registry)

        resp = await _like_post(client, post["id"])

        _assert_code(resp, httpx.codes.OK)
        _assert_body(resp, {"links": [{"rel": "unlike", "href": f"/posts/{post['id']}/like", "action": "DELETE"}]})
        _assert_liked(catalog, post["id"], username)
        _assert_activity_tracked(registry, username)

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
        _assert_activity_tracked(registry, username)


class TestDELETELikes:
    """Test post resource DELETE like endpoint."""

    async def test_unliking_post(
        self, client: httpx.AsyncClient, catalog: StubPostsCatalog, registry: StubUsersRegistry
    ):
        post = _random_post()
        catalog.add_post(post)
        username = _authorize(client, registry)
        catalog.add_like(username, post["id"])

        resp = await _unlike_post(client, post["id"])

        _assert_code(resp, httpx.codes.OK)
        _assert_body(resp, {"links": [{"rel": "like", "href": f"/posts/{post['id']}/like", "action": "POST"}]})
        _assert_unliked(catalog, post["id"], username)
        _assert_activity_tracked(registry, username)

    async def test_with_unauth_user(self, client: httpx.AsyncClient, catalog: StubPostsCatalog):
        post = _random_post()
        catalog.add_post(post)

        resp = await _unlike_post(client, post["id"])

        _assert_code(resp, httpx.codes.UNAUTHORIZED)

    async def test_without_like_from_user(
        self, client: httpx.AsyncClient, catalog: StubPostsCatalog, registry: StubUsersRegistry
    ):
        post = _random_post()
        catalog.add_post(post)
        username = _authorize(client, registry)

        resp = await _unlike_post(client, post["id"])

        _assert_code(resp, httpx.codes.FORBIDDEN)
        _assert_body(resp, {"detail": "You did not liked this post"})
        _assert_activity_tracked(registry, username)


class TestGETAnalytics:
    async def test_retrieving_analytics(self, client: httpx.AsyncClient, catalog: StubPostsCatalog):
        count = fake.pyint(min_value=1)
        catalog.count = count
        start = fake.date_object()
        end = fake.date_object()

        resp = await _get_analytics(client, start, end)

        _assert_code(resp, httpx.codes.OK)
        _assert_body(resp, {"likes": count})
        _assert_analytics(catalog, start, end)

    async def test_without_dates(self, client: httpx.AsyncClient, catalog: StubPostsCatalog):
        count = fake.pyint(min_value=1)
        catalog.count = count
        start = None
        end = None

        resp = await _get_analytics(client, start, end)

        _assert_code(resp, httpx.codes.OK)
        _assert_body(resp, {"likes": count})
        _assert_analytics(catalog, start, end)


def _random_signup_request() -> dict:
    return {"username": fake.pystr(), "password": fake.pystr()}


def _new_login_request(user: dict) -> dict:
    return {"username": user["username"], "password": user["password"]}


def _random_post_request() -> dict:
    return {"title": fake.pystr(), "description": fake.pystr()}


def _random_user() -> dict:
    return {
        "username": fake.pystr(),
        "password": fake.pystr(),
        "last_login": fake.date_object(),
        "last_activity": fake.date_object(),
    }


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
    return await client.post("/users/login", data=request)


async def _get_activity(client: httpx.AsyncClient) -> httpx.Response:
    return await client.get("/users/activity")


async def _make_post(client: httpx.AsyncClient, post: dict) -> httpx.Response:
    return await client.post("/posts", json=post)


async def _get_post(client: httpx.AsyncClient, post_id: posts.ID) -> httpx.Response:
    return await client.get(f"/posts/{post_id}")


async def _like_post(client: httpx.AsyncClient, post_id: posts.ID) -> httpx.Response:
    return await client.post(f"/posts/{post_id}/like")


async def _unlike_post(client: httpx.AsyncClient, post_id: posts.ID) -> httpx.Response:
    return await client.delete(f"/posts/{post_id}/like")


async def _get_analytics(
    client: httpx.AsyncClient, start: datetime.date | None, end: datetime.date | None
) -> httpx.Response:
    params = {}

    if start is not None:
        params.update(date_from=start)

    if end is not None:
        params.update(date_to=end)

    return await client.get("/analytics", params=params)


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
    assert len(catalog.like_calls) == 1, f"Have {len(catalog.like_calls)} calls to like, want 1"
    err = f"Have {catalog.like_calls[0]} args to like call, want ({post_id}, {username})"
    assert catalog.like_calls[0] == (post_id, username), err


def _assert_no_likes(catalog: StubPostsCatalog):
    assert not catalog.like_calls, "Catalog has likes"


def _assert_unliked(catalog: StubPostsCatalog, post_id: posts.ID, username: str):
    assert len(catalog.unlike_calls) == 1, f"Have {len(catalog.unlike_calls)} calls to unlike, want 1"
    err = f"Have {catalog.unlike_calls[0]} args to unlike call, want ({post_id}, {username})"
    assert catalog.unlike_calls[0] == (post_id, username), err


def _assert_activity_tracked(registry: StubUsersRegistry, username: str):
    assert len(registry.track_calls) == 1, f"Have {len(registry.track_calls)} calls to track user, want 1"
    assert registry.track_calls[0] == username, f"Have {registry.track_calls[0]} args to track call, want {username}"


def _assert_analytics(catalog: StubPostsCatalog, start: datetime.date | None, end: datetime.date | None):
    assert len(catalog.analytics_calls) == 1, f"Have {len(catalog.analytics_calls)} calls to analytics, want 1"
    err = f"Have {catalog.analytics_calls!r} args to analytics call, want ({start!r}, {end!r})"
    assert catalog.analytics_calls[0] == (start, end), err
