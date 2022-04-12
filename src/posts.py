"""Posts module."""


from typing import Optional

import pydantic
import sqlalchemy as sa
from sqlalchemy import exc
from sqlalchemy.engine import base


ID = int


metadata = sa.MetaData()
users_table = sa.Table(
    "users",
    metadata,
    sa.Column("username", sa.String, primary_key=True),
    sa.Column("password", sa.String, nullable=False),
)
table = sa.Table(
    "posts",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("author", None, sa.ForeignKey("users.username")),
    sa.Column("title", sa.String, nullable=False),
    sa.Column("description", sa.String, nullable=False),
)
likes_table = sa.Table(
    "likes",
    metadata,
    sa.Column("user", None, sa.ForeignKey("users.username")),
    sa.Column("post", None, sa.ForeignKey("posts.id")),
    sa.UniqueConstraint("user", "post"),
)


class AlreadyLiked(Exception):
    """User already liked the post."""


class AuthorLiked(Exception):
    """User already liked the post."""


class NotLiked(Exception):
    """User did not liked the post."""


class NotFound(Exception):
    """Post not found in catalog."""


class MakePostRequest(pydantic.BaseModel):
    """Request for a new post."""

    title: str
    description: str


class Catalog:
    """Catalog of users posts."""

    def __init__(self, connection: base.Connection):
        self._connection = connection

    def make_post(self, author: str, req: MakePostRequest) -> ID:
        """Make a new post.

        Args:
            author: user making new post.
            req: new post request.
        Returns:
            New post ID.
        """
        stmt = table.insert().values(author=author, title=req.title, description=req.description)
        result = self._connection.execute(stmt)
        return result.inserted_primary_key.id

    def get(self, post_id: ID) -> Optional[dict]:
        """Get post from catalog.

        Args:
            post_id: unique ID to look for.
        Returns:
            Saved post in catalog if found.
        """
        select = table.select().where(table.c.id == post_id)
        result = self._connection.execute(select).fetchone()

        if not result:
            return None

        return dict(result)

    def has_like(self, post_id: ID, username: str) -> bool:
        """Check whether the user has liked the post.

        Args:
            post_id: unique ID to look for.
            username: checking user.
        Returns:
            Whether the user has liked the post.
        """
        select = likes_table.select().where(likes_table.c.post == post_id and likes_table.c.user == username)
        result = self._connection.execute(select)
        return bool(result.fetchone())

    def like(self, post_id: ID, username):
        """Like post.

        Args:
            post_id: unique ID to look for.
            username: checking user.
        Raises:
            NotFound: post not found in catalog.
            AuthorLiked: author attempted to like the post.
            AlreadyLiked: user attempted to like the post he already liked.
        """
        post = self.get(post_id)

        if post is None:
            raise NotFound

        if post["author"] == username:
            raise AuthorLiked

        insert = likes_table.insert().values(post=post_id, user=username)

        try:
            self._connection.execute(insert)
        except exc.IntegrityError:
            raise AlreadyLiked

    def unlike(self, post_id: ID, username):
        """Unlike post.

        Args:
            post_id: unique ID to look for.
            username: user has liked post before.
        """
        ...
