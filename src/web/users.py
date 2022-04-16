from __future__ import annotations
from typing import Generator

import fastapi
from fastapi import security
import pydantic

import tables
import users


router = fastapi.APIRouter(prefix="/users", tags=["users"])


def registry() -> Generator[users.Registry, None, None]:
    with tables.engine.begin() as connection:
        yield users.Registry(connection)


class SignupRequest(pydantic.BaseModel):
    """Request for registering new user."""

    username: str
    password: str


oauth2_scheme = security.OAuth2PasswordBearer(tokenUrl="/users/login", auto_error=False)


def current_user(
    token: str | None = fastapi.Depends(oauth2_scheme), registry: users.Registry = fastapi.Depends(registry)
) -> str:
    """Dependency for retrieving username from a request."""
    if not token:
        raise fastapi.HTTPException(fastapi.status.HTTP_401_UNAUTHORIZED)

    try:
        username = registry.authenticate(token)
    except users.Unauthorized:
        raise fastapi.HTTPException(fastapi.status.HTTP_403_FORBIDDEN)

    return username


def optional_user(
    token: str | None = fastapi.Depends(oauth2_scheme), registry: users.Registry = fastapi.Depends(registry)
) -> str | None:
    """Dependency for optional retrieving username from a request."""
    if not token:
        return None

    return current_user(token, registry)


async def track_activity(
    username: str | None = fastapi.Depends(optional_user),
    registry: users.Registry = fastapi.Depends(registry),
):
    """Dependency for tracking user activity."""
    if username is None:
        return

    registry.track_activity(username)


@router.post("", status_code=201)
def signup(req: SignupRequest, registry: users.Registry = fastapi.Depends(registry)):
    registry.signup(req.username, req.password)
    return {"links": [{"rel": "login", "href": "/login", "action": "POST"}]}


@router.post("/login")
def login(
    form_data: security.OAuth2PasswordRequestForm = fastapi.Depends(),
    registry: users.Registry = fastapi.Depends(registry),
):
    try:
        response = {"access_token": registry.login(form_data.username, form_data.password), "token_type": "bearer"}
    except users.Unauthorized:
        raise fastapi.HTTPException(fastapi.status.HTTP_401_UNAUTHORIZED)
    registry.track_activity(form_data.username)
    return response


@router.get("/activity")
def get_activity(username: str = fastapi.Depends(current_user), registry: users.Registry = fastapi.Depends(registry)):
    last_login, last_activity = registry.get_activities(username)
    return {"last_login": last_login, "last_activity": last_activity}
