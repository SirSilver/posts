from __future__ import annotations

from typing import Optional, Protocol

import fastapi
import pydantic


PostID = int


class UsersRegistry(Protocol):
    """Users registry."""

    def signup(self, req: SignupRequest):
        """Signup new user.

        Args:
            req: new signup user request.
        """
        ...

    def login(self, username: str, password: str) -> str:
        """Login registered user.

        Args:
            username: user login identificator.
            password: user password to match with the one in registry.
        Returns:
            Access auth token.
        """
        ...


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
    app.include_router(users_router)
    app.include_router(posts_router)
    return app


users_router = fastapi.APIRouter(prefix="/users", tags=["users"])


def registry() -> UsersRegistry:
    ...


class SignupRequest(pydantic.BaseModel):
    """Request for registering new user."""

    username: str
    password: str


@users_router.post("", status_code=201)
def signup(req: SignupRequest, registry: UsersRegistry = fastapi.Depends(registry)):
    registry.signup(req)
    return {"links": [{"rel": "login", "href": "/login", "action": "POST"}]}


@users_router.post("/login")
def login(req: SignupRequest, registry: UsersRegistry = fastapi.Depends(registry)):
    return {"token": registry.login(req.username, req.password)}


posts_router = fastapi.APIRouter(prefix="/posts", tags=["posts"])


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


@posts_router.post("", status_code=201)
def create_post(req: PostRequest, response: fastapi.Response, catalog: PostCatalog = fastapi.Depends(catalog)):
    post_id = catalog.make_post(req)
    response.headers["location"] = f"/posts/{post_id}"


@posts_router.get("/{post_id}", response_model=PostResponse)
def get_post(post_id: PostID, catalog: PostCatalog = fastapi.Depends(catalog)):
    post = catalog.get(post_id)

    if post is None:
        raise fastapi.HTTPException(status_code=fastapi.status.HTTP_404_NOT_FOUND)

    return post
