"""Posts module."""


import datetime
from typing import Optional

import pydantic
import sqlalchemy as sa
from sqlalchemy import exc
from sqlalchemy.engine import base

import tables


ID = int


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
        stmt = sa.insert(tables.posts).values(author=author, title=req.title, description=req.description)
        result = self._connection.execute(stmt)
        return result.inserted_primary_key.id

    def get(self, post_id: ID) -> Optional[dict]:
        """Get post from catalog.

        Args:
            post_id: unique ID to look for.
        Returns:
            Saved post in catalog if found.
        """
        select = sa.select(tables.posts).where(tables.posts.c.id == post_id)
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
        select = sa.select(tables.likes).where(tables.likes.c.post == post_id and tables.likes.c.user == username)
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

        insert = sa.insert(tables.likes).values(post=post_id, user=username)

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
        if not self.has_like(post_id, username):
            raise NotLiked

        delete = sa.delete(tables.likes).where(tables.likes.c.post == post_id and tables.likes.c.user == username)
        self._connection.execute(delete)

    def analytics(self, start: datetime.date | None = None, end: datetime.date | None = None) -> int:
        """Get aggregated likes count.

        Args:
            start: start date of aggregating.
            end: end date of aggregating.
        Returns:
            Number of likes made in given period.
        """
        ...
