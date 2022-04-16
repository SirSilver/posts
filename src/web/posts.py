"""Posts web REST API resources."""


from __future__ import annotations

import fastapi
import pydantic

import posts
import tables
from web import users


class Link(pydantic.BaseModel):
    """Response model for returning links corresponding to HATEOAS."""

    rel: str
    href: str
    action: str


class PostResponse(pydantic.BaseModel):
    """Response model for retrieving post details."""

    id: int
    author: str
    title: str
    description: str
    links: list[Link] = pydantic.Field(default_factory=list)


router = fastapi.APIRouter(prefix="/posts", tags=["posts"], dependencies=[fastapi.Depends(users.track_activity)])


async def catalog() -> posts.Catalog:
    connection = tables.engine.connect()
    return posts.Catalog(connection)


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
def get_post(
    post_id: posts.ID,
    catalog: posts.Catalog = fastapi.Depends(catalog),
    username: str = fastapi.Depends(users.optional_user),
):
    post = catalog.get(post_id)

    if post is None:
        raise fastapi.HTTPException(status_code=fastapi.status.HTTP_404_NOT_FOUND)

    links = []

    resp = post | {"links": links}

    if not username or post["author"] == username:
        return resp

    if catalog.has_like(post["id"], username):
        links.append(_link("unlike", f"/posts/{post_id}/like", "DELETE"))
    else:
        links.append(_link("like", f"/posts/{post_id}/like", "POST"))

    return resp


@router.post("/{post_id}/like")
def like(
    post_id: posts.ID,
    catalog: posts.Catalog = fastapi.Depends(catalog),
    username: str = fastapi.Depends(users.current_user),
):
    try:
        catalog.like(post_id, username)
    except posts.AlreadyLiked:
        raise fastapi.HTTPException(fastapi.status.HTTP_403_FORBIDDEN, "You already liked this post")

    return {"links": [_link("unlike", f"/posts/{post_id}/like", "DELETE")]}


@router.delete("/{post_id}/like", status_code=fastapi.status.HTTP_200_OK)
def unlike(
    post_id: posts.ID,
    catalog: posts.Catalog = fastapi.Depends(catalog),
    username: str = fastapi.Depends(users.current_user),
):
    try:
        catalog.unlike(post_id, username)
    except posts.NotLiked:
        raise fastapi.HTTPException(fastapi.status.HTTP_403_FORBIDDEN, "You did not liked this post")

    return {"links": [_link("like", f"/posts/{post_id}/like", "POST")]}


def _link(rel: str, href: str, action: str) -> dict:
    return {"rel": rel, "href": href, "action": action}
