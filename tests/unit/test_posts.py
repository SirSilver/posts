import datetime
import faker
import pytest
import sqlalchemy
from sqlalchemy.engine import base

import posts


fake = faker.Faker()


def test_making_new_post(engine: sqlalchemy.engine.Engine):
    with engine.begin() as connection:
        catalog = posts.Catalog(connection)
        author = _random_user()
        request = _new_post_request()

        post_id = catalog.make_post(author, request)
        post = _select_post(connection, post_id)

        _assert_post_saved(post_id, author, request, post)


class TestGetPost:
    def test_retrieving_post(self, engine: sqlalchemy.engine.Engine):
        with engine.begin() as connection:
            catalog = posts.Catalog(connection)
            post = _new_post()
            _insert_post(connection, post)

            result = catalog.get(post["id"])

            assert result is not None
            _assert_post(post, result)

    def test_with_non_existent_post(self, engine: sqlalchemy.engine.Engine):
        with engine.begin() as connection:
            catalog = posts.Catalog(connection)

            result = catalog.get(fake.pyint(min_value=1))

            assert result is None, "Post does not have a like from user"


class TestHasLike:
    def test_with_existing_like(self, engine: sqlalchemy.engine.Engine):
        with engine.begin() as connection:
            catalog = posts.Catalog(connection)
            username = _random_user()
            post = _new_post(username)
            _insert_post(connection, post)
            _like_post(connection, post, username)

            result = catalog.has_like(post["id"], username)

            assert result is True

    def test_with_non_existing_like(self, engine: sqlalchemy.engine.Engine):
        with engine.begin() as connection:
            catalog = posts.Catalog(connection)
            username = _random_user()
            post = _new_post()
            _insert_post(connection, post)

            result = catalog.has_like(post["id"], username)

            assert result is False, "Post has a like from user"


class TestLike:
    def test_creates_like(self, engine: sqlalchemy.engine.Engine):
        with engine.begin() as connection:
            catalog = posts.Catalog(connection)
            username = _random_user()
            post = _new_post()
            _insert_post(connection, post)

            catalog.like(post["id"], username)

            _assert_liked(connection, post["id"], username)

    def test_with_non_existent_post(self, engine: sqlalchemy.engine.Engine):
        with engine.begin() as connection:
            catalog = posts.Catalog(connection)
            username = _random_user()
            post = _new_post()

            with pytest.raises(posts.NotFound):
                catalog.like(post["id"], username)

    def test_with_existing_like(self, engine: sqlalchemy.engine.Engine):
        with engine.begin() as connection:
            catalog = posts.Catalog(connection)
            username = _random_user()
            post = _new_post()
            _insert_post(connection, post)
            _like_post(connection, post, username)

            with pytest.raises(posts.AlreadyLiked):
                catalog.like(post["id"], username)

    def test_with_user_liked_another_post(self, engine: sqlalchemy.engine.Engine):
        with engine.begin() as connection:
            catalog = posts.Catalog(connection)
            username = _random_user()
            liked_post = _new_post()
            _insert_post(connection, liked_post)
            _like_post(connection, liked_post, username)
            post = _new_post()
            _insert_post(connection, post)

            catalog.like(post["id"], username)

            _assert_liked(connection, post["id"], username)

    def test_with_author(self, engine: sqlalchemy.engine.Engine):
        with engine.begin() as connection:
            catalog = posts.Catalog(connection)
            username = _random_user()
            post = _new_post(username)
            _insert_post(connection, post)

            with pytest.raises(posts.AuthorLiked):
                catalog.like(post["id"], username)


class TestUnlike:
    def test_deletes_like(self, engine: sqlalchemy.engine.Engine):
        with engine.begin() as connection:
            catalog = posts.Catalog(connection)
            username = _random_user()
            post = _new_post()
            _insert_post(connection, post)
            _like_post(connection, post, username)

            catalog.unlike(post["id"], username)

            _assert_unliked(connection, post["id"], username)

    def test_with_unliked_post(self, engine: sqlalchemy.engine.Engine):
        with engine.begin() as connection:
            catalog = posts.Catalog(connection)
            username = _random_user()
            post = _new_post()
            _insert_post(connection, post)

            with pytest.raises(posts.NotLiked):
                catalog.unlike(post["id"], username)


class TestAnalytics:
    def test_aggregates_likes(self, engine: sqlalchemy.engine.Engine):
        with engine.begin() as connection:
            catalog = posts.Catalog(connection)
            post = _new_post()
            _insert_post(connection, post)
            count = fake.pyint(min_value=1, max_value=10)

            for _ in range(count):
                _like_post(connection, post, _random_user())

            likes = catalog.analytics()

            assert likes == count, "Likes were aggregated wrong"

    def test_with_date_range(self, engine: sqlalchemy.engine.Engine):
        with engine.begin() as connection:
            catalog = posts.Catalog(connection)
            post = _new_post()
            _insert_post(connection, post)
            count = fake.pyint(min_value=1, max_value=10)
            date_to = fake.date_object()
            date_from = fake.date_object(date_to)

            for _ in range(count):
                _like_post_date(connection, post, _random_user(), fake.date_between(date_from, date_to))

            for _ in range(fake.pyint(min_value=1, max_value=10)):
                _like_post_date(connection, post, _random_user(), fake.date_object(date_from))

            likes = catalog.analytics(date_from, date_to)

            assert likes == count, "Likes were aggregated wrong"

    def test_with_null_date_from(self, engine: sqlalchemy.engine.Engine):
        with engine.begin() as connection:
            catalog = posts.Catalog(connection)
            post = _new_post()
            _insert_post(connection, post)
            count = fake.pyint(min_value=1, max_value=10)
            date_from = fake.past_date()
            date_to = fake.past_date(date_from)

            for _ in range(count):
                _like_post_date(connection, post, _random_user(), fake.date_between(date_from, date_to))

            for _ in range(count):
                _like_post_date(connection, post, _random_user(), fake.future_date())

            likes = catalog.analytics(None, date_to)

            assert likes == count, "Likes were aggregated wrong"

    def test_with_null_date_to(self, engine: sqlalchemy.engine.Engine):
        with engine.begin() as connection:
            catalog = posts.Catalog(connection)
            post = _new_post()
            _insert_post(connection, post)
            count = fake.pyint(min_value=1, max_value=10)
            date_from = fake.past_date()
            date_to = fake.past_date(date_from)

            for _ in range(count):
                _like_post_date(connection, post, _random_user(), fake.date_between(date_from, date_to))

            for _ in range(count):
                _like_post_date(connection, post, _random_user(), fake.future_date())

            likes = catalog.analytics(date_from, None)

            assert likes == 2 * count, "Likes were aggregated wrong"


def _random_user() -> str:
    return fake.pystr()


def _new_post_request() -> posts.MakePostRequest:
    return posts.MakePostRequest(title=fake.pystr(), description=fake.pystr())


def _new_post(author: str | None = None) -> dict:
    if author is None:
        author = _random_user()

    return {
        "id": fake.pyint(min_value=1),
        "author": author,
        "title": fake.pystr(),
        "description": fake.pystr(),
    }


def _select_post(connection: base.Connection, post_id: posts.ID) -> dict | None:
    text = "SELECT id, author, title, description FROM posts WHERE posts.id == :post_id"
    select = sqlalchemy.text(text).bindparams(post_id=post_id)
    result = connection.execute(select).fetchone()
    if not result:
        return None
    return dict(result)


def _insert_post(connection: base.Connection, post: dict):
    text = "INSERT INTO posts (id, author, title, description) VALUES (:id, :author, :title, :description)"
    values = dict(id=post["id"], author=post["author"], title=post["title"], description=post["description"])
    insert = sqlalchemy.text(text).bindparams(**values)
    connection.execute(insert)


def _like_post(connection: base.Connection, post: dict, author: str):
    text = "INSERT INTO likes (user, post) VALUES (:user, :post)"
    insert = sqlalchemy.text(text).bindparams(user=author, post=post["id"])
    connection.execute(insert)


def _like_post_date(connection: base.Connection, post: dict, author: str, date: datetime.date):
    text = "INSERT INTO likes (user, post, date) VALUES (:user, :post, :date)"
    insert = sqlalchemy.text(text).bindparams(user=author, post=post["id"], date=date)
    connection.execute(insert)


def _assert_post_saved(post_id: posts.ID, author: str, request: posts.MakePostRequest, want: dict | None):
    assert want is not None
    assert {"id": post_id, "author": author, "title": request.title, "description": request.description} == want


def _assert_post(post: dict, want: dict):
    assert post == want, "Received wrong post"


def _assert_liked(connection: base.Connection, post_id: posts.ID, username: str):
    text = "SELECT 1 FROM likes WHERE likes.post == :post_id AND likes.user == :username"
    select = sqlalchemy.text(text).bindparams(post_id=post_id, username=username)
    assert bool(connection.execute(select).fetchone()) is True, "Post does not have like from user"


def _assert_unliked(connection: base.Connection, post_id: posts.ID, username: str):
    text = "SELECT 1 FROM likes WHERE likes.post == :post_id AND likes.user == :username"
    select = sqlalchemy.text(text).bindparams(post_id=post_id, username=username)
    assert bool(connection.execute(select).fetchone()) is False, "Post still has a like from user"
