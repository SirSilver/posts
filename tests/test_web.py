from __future__ import annotations

from typing import TYPE_CHECKING

import faker
import httpx

if TYPE_CHECKING:
    from tests.conftest import StubPostsCatalog

fake = faker.Faker()


class TestPOSTPosts:
    """Test posts resource POST endpoint."""

    async def test_creating_post(self, client: httpx.AsyncClient, catalog: StubPostsCatalog):
        post = _random_post()

        resp = await _make_post(client, post)

        _assert_code(resp, httpx.codes.CREATED)
        _assert_location(resp, "/posts/1")
        _assert_posted(catalog, post)


def _random_post() -> dict:
    return {"title": fake.pystr(), "description": fake.pystr()}


async def _make_post(client: httpx.AsyncClient, post: dict) -> httpx.Response:
    return await client.post("/posts", json=post)


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
