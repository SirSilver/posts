"""Posts web REST API resources."""


from __future__ import annotations

import fastapi
import pydantic

import posts
from web import users


class PostResponse(pydantic.BaseModel):
    """Response model for retrieving post details."""

    id: int
    author: str
    title: str
    description: str


router = fastapi.APIRouter(prefix="/posts", tags=["posts"])


def catalog() -> posts.Catalog:
    ...


@router.post("", status_code=201)
def create_post(
    req: posts.MakePostRequest,
    response: fastapi.Response,
    catalog: posts.Catalog = fastapi.Depends(catalog),
    username: str = fastapi.Depends(users.current_user),
):
    post_id = catalog.make_post(username, req)
    response.headers["location"] = f"/posts/{post_id}"


@router.get("/{post_id}", response_model=PostResponse)
def get_post(post_id: posts.ID, catalog: posts.Catalog = fastapi.Depends(catalog)):
    post = catalog.get(post_id)

    if post is None:
        raise fastapi.HTTPException(status_code=fastapi.status.HTTP_404_NOT_FOUND)

    return post
