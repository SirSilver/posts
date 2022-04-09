"""Web application."""


import fastapi

from web import posts, users


def create_app() -> fastapi.FastAPI:
    app = fastapi.FastAPI()
    app.include_router(users.router)
    app.include_router(posts.router)
    return app
