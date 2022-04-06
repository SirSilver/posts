import dataclasses
from typing import Optional

import faker
import httpx

import web


fake = faker.Faker()


class TestPOSTPosts:
    """Test posts resource POST endpoint."""

    async def test_creating_post(self):
        catalog = _StubPostsCatalog()
        client = _get_client(catalog)
        post = _random_post()

        resp = await client.post("/posts", json=post)

        _assert_code(resp, httpx.codes.CREATED)
        _assert_location(resp, "/posts/1")
        _assert_posted(catalog, post)


@dataclasses.dataclass
class _StubPostsCatalog:
    """Stub implementation of posts catalog for testing."""

    post_calls: list[dict] = dataclasses.field(default_factory=list)

    def make_post(self, req: web.PostRequest):
        """Make a new post."""
        self.post_calls.append(req.dict())


def _get_client(catalog: Optional[_StubPostsCatalog] = None) -> httpx.AsyncClient:
    if catalog is None:
        catalog = _StubPostsCatalog()

    app = web.create_app()
    app.dependency_overrides[web.catalog] = lambda: catalog

    return httpx.AsyncClient(app=app, base_url="https://testserver")


def _random_post() -> dict:
    return {"title": fake.pystr(), "description": fake.pystr()}


def _assert_code(resp: httpx.Response, want: int):
    have = resp.status_code
    assert have == want, f"Invalid status code received\nhave {have}\nwant {want}"


def _assert_location(resp: httpx.Response, want: str):
    assert "location" in resp.headers, "Missing location header"
    have = resp.headers["location"]
    assert have == want, f"Invalid location received\nhave {have}\nwant {want}"


def _assert_posted(catalog: _StubPostsCatalog, post: dict):
    assert len(catalog.post_calls) == 1, f"Have {len(catalog.post_calls)} calls to post, want 1"
    assert catalog.post_calls[0] == post, f"Didn't post correct message, have {catalog.post_calls[0]}, want {post}"
