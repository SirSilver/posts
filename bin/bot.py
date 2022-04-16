from __future__ import annotations

import asyncio
import dataclasses
import itertools
import json
import random
from typing import Iterable
from urllib import parse

import faker
import httpx


HOST = "http://localhost:8000"
SIGNUP_URL = parse.urljoin(HOST, "/users")
LOGIN_URL = parse.urljoin(HOST, "/users/login")
MAKE_POST_URL = parse.urljoin(HOST, "/posts")
LIKE_POST_URL = parse.urljoin(HOST, "/posts/{id}/like")


fake = faker.Faker()


async def main():
    config = _load_config("config.json")
    users_number = fake.pyint(min_value=1, max_value=config["number_of_users"])
    signups = (_signup(f"user{i}", f"password{i}") for i in range(users_number))
    users = await asyncio.gather(*signups)
    logins = (u.login() for u in users)
    await asyncio.gather(*logins)
    posts_number = fake.pyint(min_value=1, max_value=config["max_posts_per_user"])
    makes = (_make_posts(u, posts_number) for u in users)
    posts = list(itertools.chain(*await asyncio.gather(*makes)))
    likes_number = fake.pyint(min_value=1, max_value=config["max_likes_per_user"])
    likes = (_like(u, posts, likes_number) for u in users)
    await asyncio.gather(*likes)


def _load_config(path: str) -> dict[str, int]:
    with open(path, "rb") as f:
        return json.loads(f.read())


async def _signup(username: str, password: str) -> User:
    user = User(name=username, password=password)
    await user.signup()
    return user


async def _make_posts(user: User, posts_number: int) -> tuple[dict, ...]:
    makes = (user.post(f"title {user.name}", f"description {user.name}") for _ in range(posts_number))
    return await asyncio.gather(*makes)


async def _like(user: User, posts: Iterable[dict], likes_number: int):
    not_author_posts = [p for p in posts if p["author"] != user.name]

    if not not_author_posts:
        return

    likes = (user.like(random.choice(not_author_posts)) for _ in range(likes_number))
    await asyncio.gather(*likes)


@dataclasses.dataclass
class User:

    name: str
    password: str
    _client: httpx.AsyncClient = dataclasses.field(default_factory=httpx.AsyncClient)

    async def signup(self):
        data = {"username": self.name, "password": self.password}
        await self._client.post(SIGNUP_URL, json=data)

    async def login(self):
        data = {"username": self.name, "password": self.password}
        resp = await self._client.post(LOGIN_URL, data=data)
        self._client.headers["Authorization"] = f"Bearer {resp.json()['access_token']}"

    async def post(self, title: str, description: str) -> dict:
        make_resp = await self._client.post(MAKE_POST_URL, json={"title": title, "description": description})
        get_resp = await self._client.get(parse.urljoin(HOST, make_resp.headers["location"]))
        return get_resp.json()

    async def like(self, post: dict):
        await self._client.post(LIKE_POST_URL.format(id=post["id"]))


if __name__ == "__main__":
    asyncio.run(main())
