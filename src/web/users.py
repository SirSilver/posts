from __future__ import annotations

import fastapi
from fastapi import security
import pydantic

import users


router = fastapi.APIRouter(prefix="/users", tags=["users"])


def registry() -> users.Registry:
    ...


class SignupRequest(pydantic.BaseModel):
    """Request for registering new user."""

    username: str
    password: str


@router.post("", status_code=201)
def signup(req: SignupRequest, registry: users.Registry = fastapi.Depends(registry)):
    registry.signup(req.username, req.password)
    return {"links": [{"rel": "login", "href": "/login", "action": "POST"}]}


@router.post("/login")
def login(req: SignupRequest, registry: users.Registry = fastapi.Depends(registry)):
    return {"token": registry.login(req.username, req.password)}


oauth2_scheme = security.OAuth2PasswordBearer(tokenUrl="/users/login", auto_error=False)


def current_user(
    token: str | None = fastapi.Depends(oauth2_scheme), registry: users.Registry = fastapi.Depends(registry)
) -> str:
    """Dependency for retrieving username from a request."""
    if not token:
        raise fastapi.HTTPException(fastapi.status.HTTP_401_UNAUTHORIZED)

    if (username := registry.authenticate(token)) is None:
        raise fastapi.HTTPException(fastapi.status.HTTP_403_FORBIDDEN)

    return username


def optional_user(
    token: str | None = fastapi.Depends(oauth2_scheme), registry: users.Registry = fastapi.Depends(registry)
) -> str | None:
    """Dependency for optional retrieving username from a request."""
    if not token:
        return None

    return current_user(token, registry)
