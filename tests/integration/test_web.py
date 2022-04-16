from typing import Sequence
import faker
import httpx


fake = faker.Faker()


async def test_users_posts_sql_web_integration(client: httpx.AsyncClient):
    author = _new_user()
    await _auth(client, author)
    request = _new_post_request()
    post_response = await _make_post(client, request)

    resp = await _get_post(client, post_response)
    _assert_post(resp, request, author)

    user = _new_user()
    await _auth(client, user)
    resp = await _get_post(client, post_response)
    _assert_post(resp, request, author, "like")

    await _like_post(client, 1)
    resp = await _get_post(client, post_response)
    _assert_post(resp, request, author, "unlike")

    await _unlike_post(client, 1)
    resp = await _get_post(client, post_response)
    _assert_post(resp, request, author, "like")


def _new_user() -> dict:
    return {"username": fake.pystr(), "password": fake.pystr()}


def _new_post_request() -> dict:
    return {"title": fake.pystr(), "description": fake.pystr()}


async def _auth(client: httpx.AsyncClient, user: dict):
    await _signup(client, user)
    resp = await _login(client, user)
    client.headers["Authorization"] = f"Bearer {resp.json()['access_token']}"


async def _signup(client: httpx.AsyncClient, user: dict) -> httpx.Response:
    return await client.post("/users", json=user)


async def _login(client: httpx.AsyncClient, user: dict) -> httpx.Response:
    return await client.post("/users/login", data=user)


async def _make_post(client: httpx.AsyncClient, post: dict) -> httpx.Response:
    return await client.post("/posts", json=post)


async def _get_post(client: httpx.AsyncClient, post_response: httpx.Response) -> httpx.Response:
    return await client.get(post_response.headers["location"])


async def _like_post(client: httpx.AsyncClient, post_id: int) -> httpx.Response:
    return await client.post(f"/posts/{post_id}/like")


async def _unlike_post(client: httpx.AsyncClient, post_id: int) -> httpx.Response:
    return await client.delete(f"/posts/{post_id}/like")


def _assert_post(response: httpx.Response, request: dict, author: dict, *rels: Sequence[str]):
    links = []

    if "like" in rels:
        links.append({"rel": "like", "href": "/posts/1/like", "action": "POST"})

    if "unlike" in rels:
        links.append({"rel": "unlike", "href": "/posts/1/like", "action": "DELETE"})

    assert response.json() == {
        "id": 1,
        "author": author["username"],
        "title": request["title"],
        "description": request["description"],
        "links": links,
    }
