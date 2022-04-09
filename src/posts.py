"""Posts module."""


from typing import Optional, Protocol

import pydantic


ID = int


class MakePostRequest(pydantic.BaseModel):
    """Request for a new post."""

    title: str
    description: str


class Catalog(Protocol):
    """Catalog of users posts."""

    def make_post(self, req: MakePostRequest) -> ID:
        """Make a new post.

        Args:
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
