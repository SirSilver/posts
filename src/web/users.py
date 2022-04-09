from __future__ import annotations

import fastapi
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
