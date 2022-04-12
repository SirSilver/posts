import faker
import sqlalchemy
from sqlalchemy.engine import base

import posts


fake = faker.Faker()
engine = sqlalchemy.create_engine("sqlite+pysqlite:///:memory:", future=True)
posts.metadata.create_all(engine)


def test_making_new_post():
    with engine.begin() as connection:
        catalog = posts.Catalog(connection)
        author = _random_user()
        request = _new_post_request()

        post_id = catalog.make_post(author, request)
        stmt = sqlalchemy.select(posts.table).where(posts.table.c.id == post_id)
        result = connection.execute(stmt)

        _assert_post_saved(post_id, author, request, result)


class TestGetPost:
    def test_retrieving_post(self):
        with engine.begin() as connection:
            catalog = posts.Catalog(connection)
            post = _new_post()
            _insert_post(connection, post)

            result = catalog.get(post["id"])

            assert result is not None
            _assert_post(post, result)

    def test_with_non_existent_post(self):
        with engine.begin() as connection:
            catalog = posts.Catalog(connection)

            result = catalog.get(fake.pyint(min_value=1))

            assert result is None, "Post does not have a like from user"


class TestHasLike:
    def test_with_existing_like(self):
        with engine.begin() as connection:
            catalog = posts.Catalog(connection)
            username = _random_user()
            post = _new_post(username)
            _insert_post(connection, post)
            _like_post(connection, post, username)

            result = catalog.has_like(post["id"], username)

            assert result is True

    def test_with_non_existing_like(self):
        with engine.begin() as connection:
            catalog = posts.Catalog(connection)
            username = _random_user()
            post = _new_post()
            _insert_post(connection, post)

            result = catalog.has_like(post["id"], username)

            assert result is False, "Post has a like from user"


def _random_user() -> str:
    return fake.pystr()


def _new_post_request() -> posts.MakePostRequest:
    return posts.MakePostRequest(title=fake.pystr(), description=fake.pystr())


def _new_post(author: str | None = None) -> dict:
    if author is None:
        author = _random_user()

    return {
        "id": fake.pyint(min_value=1),
        "author": _random_user(),
        "title": fake.pystr(),
        "description": fake.pystr(),
    }


def _insert_post(connection: base.Connection, post: dict):
    text = "INSERT INTO posts (id, author, title, description) VALUES (:id, :author, :title, :description)"
    values = dict(id=post["id"], author=post["author"], title=post["title"], description=post["description"])
    insert = sqlalchemy.text(text).bindparams(**values)
    connection.execute(insert)


def _like_post(connection: base.Connection, post: dict, author: str):
    text = "INSERT INTO likes (user, post) VALUES (:user, :post)"
    insert = sqlalchemy.text(text).bindparams(user=author, post=post["id"])
    connection.execute(insert)


def _assert_post_saved(post_id: posts.ID, author: str, request: posts.MakePostRequest, result):
    assert (post_id, author, request.title, request.description) == result.fetchone()


def _assert_post(post: dict, want: dict):
    assert post == want, "Received wrong post"
