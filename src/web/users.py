from __future__ import annotations

from typing import Protocol

import fastapi
import pydantic


class UsersRegistry(Protocol):
    """Users registry."""

    def signup(self, username: str, password: str):
        """Signup new user.

        Args:
            username: user login identificator.
            password: user auth password.
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


router = fastapi.APIRouter(prefix="/users", tags=["users"])


def registry() -> UsersRegistry:
    ...


class SignupRequest(pydantic.BaseModel):
    """Request for registering new user."""

    username: str
    password: str


@router.post("", status_code=201)
def signup(req: SignupRequest, registry: UsersRegistry = fastapi.Depends(registry)):
    registry.signup(req.username, req.password)
    return {"links": [{"rel": "login", "href": "/login", "action": "POST"}]}


@router.post("/login")
def login(req: SignupRequest, registry: UsersRegistry = fastapi.Depends(registry)):
    return {"token": registry.login(req.username, req.password)}
