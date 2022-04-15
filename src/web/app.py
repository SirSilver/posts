"""Web application."""


import fastapi

from web import analytics, posts, users


def create_app() -> fastapi.FastAPI:
    app = fastapi.FastAPI()
    app.include_router(users.router)
    app.include_router(posts.router)
    app.include_router(analytics.router)
    return app
