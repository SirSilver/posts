"""Posts module."""


from typing import Optional

import pydantic
import sqlalchemy
from sqlalchemy.engine import base


ID = int


metadata = sqlalchemy.MetaData()
users_table = sqlalchemy.Table(
    "users",
    metadata,
    sqlalchemy.Column("username", sqlalchemy.String, primary_key=True),
    sqlalchemy.Column("password", sqlalchemy.String, nullable=False),
)
table = sqlalchemy.Table(
    "posts",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("author", None, sqlalchemy.ForeignKey("users.username")),
    sqlalchemy.Column("title", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("description", sqlalchemy.String, nullable=False),
)


class AlreadyLiked(Exception):
    """User already liked the post."""


class NotLiked(Exception):
    """User did not liked the post."""


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
        ...

    def has_like(self, post_id: ID, username: str) -> bool:
        """Check whether the user has liked the post.

        Args:
            post_id: unique ID to look for.
            username: checking user.
        Returns:
            Whether the user has liked the post.
        """
        ...

    def like(self, post_id: ID, username):
        """Like post.

        Args:
            post_id: unique ID to look for.
            username: checking user.
        """
        ...

    def unlike(self, post_id: ID, username):
        """Unlike post.

        Args:
            post_id: unique ID to look for.
            username: user has liked post before.
        """
        ...
