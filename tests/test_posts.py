import faker
import sqlalchemy

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


def _random_author() -> str:
    return fake.pystr()


def _new_post_request() -> posts.MakePostRequest:
    return posts.MakePostRequest(title=fake.pystr(), description=fake.pystr())


def _assert_post_saved(post_id: posts.ID, author: str, request: posts.MakePostRequest, result):
    assert (post_id, author, request.title, request.description) == result.fetchone()
