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
        author = _random_author()
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

            assert result is None


def _random_author() -> str:
    return fake.pystr()


def _new_post_request() -> posts.MakePostRequest:
    return posts.MakePostRequest(title=fake.pystr(), description=fake.pystr())


def _new_post() -> dict:
    return {
        "id": fake.pyint(min_value=1),
        "author": _random_author(),
        "title": fake.pystr(),
        "description": fake.pystr(),
    }


def _insert_post(connection: base.Connection, post: dict):
    insert = posts.table.insert().values(
        id=post["id"], author=post["author"], title=post["title"], description=post["description"]
    )
    connection.execute(insert)


def _assert_post_saved(post_id: posts.ID, author: str, request: posts.MakePostRequest, result):
    assert (post_id, author, request.title, request.description) == result.fetchone()


def _assert_post(post: dict, want: dict):
    assert post == want, "Received wrong post"
