from __future__ import annotations

from typing import Protocol

import fastapi
import pydantic


PostID = int


class PostCatalog(Protocol):
    """Catalog of users posts."""

    def make_post(self, req: PostRequest) -> PostID:
        """Make a new post.

        Args:
            req: new post request
        Returns:
            New post ID.
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


@router.post("/posts", status_code=201)
def create_post(req: PostRequest, response: fastapi.Response, catalog: PostCatalog = fastapi.Depends(catalog)):
    post_id = catalog.make_post(req)
    response.headers["location"] = f"/posts/{post_id}"
