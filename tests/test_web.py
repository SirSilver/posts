from __future__ import annotations

from typing import TYPE_CHECKING

import faker
import httpx

if TYPE_CHECKING:
    from tests.conftest import StubPostsCatalog
    import web

fake = faker.Faker()


class TestPOSTPosts:
    """Test posts resource POST endpoint."""

    async def test_creating_post(self, client: httpx.AsyncClient, catalog: StubPostsCatalog):
        request = _random_post_request()

        resp = await _make_post(client, request)

        _assert_code(resp, httpx.codes.CREATED)
        _assert_location(resp, "/posts/1")
        _assert_posted(catalog, request)


class TestGETPost:
    """Test post resource GET endpoint."""

    async def test_retrieving_post(self, client: httpx.AsyncClient, catalog: StubPostsCatalog):
        post = _random_post()
        catalog.add_post(post)

        resp = await _get_post(client, post["id"])

        _assert_code(resp, httpx.codes.OK)
        _assert_body(resp, post)

    async def test_with_non_existent_post(self, client: httpx.AsyncClient):
        resp = await _get_post(client, fake.pyint(min_value=1))

        _assert_code(resp, httpx.codes.NOT_FOUND)
        _assert_body(resp, {"detail": "Not Found"})


def _random_post_request() -> dict:
    return {"title": fake.pystr(), "description": fake.pystr()}


def _random_post() -> dict:
    return {"id": fake.pyint(min_value=1)} | _random_post_request()


async def _make_post(client: httpx.AsyncClient, post: dict) -> httpx.Response:
    return await client.post("/posts", json=post)


async def _get_post(client: httpx.AsyncClient, post_id: web.PostID) -> httpx.Response:
    return await client.get(f"/posts/{post_id}")


def _assert_code(resp: httpx.Response, want: int):
    have = resp.status_code
    assert have == want, f"Invalid status code received\nhave {have}\nwant {want}"


def _assert_location(resp: httpx.Response, want: str):
    assert "location" in resp.headers, "Missing location header"
    have = resp.headers["location"]
    assert have == want, f"Invalid location received\nhave {have}\nwant {want}"


def _assert_posted(catalog: StubPostsCatalog, post: dict):
    assert len(catalog.post_calls) == 1, f"Have {len(catalog.post_calls)} calls to post, want 1"
    assert catalog.post_calls[0] == post, f"Didn't post correct message, have {catalog.post_calls[0]}, want {post}"


def _assert_body(resp: httpx.Response, body: dict):
    assert resp.json() == body, f"Didn't get correct response, have {resp.json()}, want {body}"
