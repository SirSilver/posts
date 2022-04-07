from __future__ import annotations

from typing import Optional, Protocol

import fastapi
import pydantic


PostID = int


class PostCatalog(Protocol):
    """Catalog of users posts."""

    def make_post(self, req: PostRequest) -> PostID:
        """Make a new post.

        Args:
            req: new post request.
        Returns:
            New post ID.
        """
        ...

    def get(self, post_id: PostID) -> Optional[dict]:
        """Get post from catalog.

        Args:
            post_id: unique ID to look for.
        Returns:
            Saved post in catalog if found.
        """
        ...


def create_app() -> fastapi.FastAPI:
    app = fastapi.FastAPI()
    app.include_router(router)
    return app


router = fastapi.APIRouter()


def catalog() -> PostCatalog:
    ...


class PostRequest(pydantic.BaseModel):
    """Request for a new post."""

    title: str
    description: str


class PostResponse(pydantic.BaseModel):
    """Response model for retrieving post details."""

    id: int
    title: str
    description: str


@router.post("/posts", status_code=201)
def create_post(req: PostRequest, response: fastapi.Response, catalog: PostCatalog = fastapi.Depends(catalog)):
    post_id = catalog.make_post(req)
    response.headers["location"] = f"/posts/{post_id}"


@router.get("/posts/{post_id}", response_model=PostResponse)
def get_post(post_id: PostID, catalog: PostCatalog = fastapi.Depends(catalog)):
    post = catalog.get(post_id)

    if post is None:
        raise fastapi.HTTPException(status_code=fastapi.status.HTTP_404_NOT_FOUND)

    return post
