"""Posts module."""


from typing import Optional, Protocol

import pydantic


ID = int


class AlreadyLiked(Exception):
    """User already liked the post."""


class NotLiked(Exception):
    """User did not liked the post."""


class MakePostRequest(pydantic.BaseModel):
    """Request for a new post."""

    title: str
    description: str


class Catalog(Protocol):
    """Catalog of users posts."""

    def make_post(self, author: str, req: MakePostRequest) -> ID:
        """Make a new post.

        Args:
            author: user making new post.
            req: new post request.
        Returns:
            New post ID.
        """
        ...

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
