import sqlalchemy as sa
from sqlalchemy import pool


engine = sa.create_engine(
    "sqlite+pysqlite:///:memory:", future=True, connect_args={"check_same_thread": False}, poolclass=pool.StaticPool
)
metadata = sa.MetaData()
users = sa.Table(
    "users",
    metadata,
    sa.Column("username", sa.String, primary_key=True),
    sa.Column("password", sa.String, nullable=False),
    sa.Column("salt", sa.String, nullable=False),
    sa.Column("last_login", sa.DateTime),
    sa.Column("last_activity", sa.DateTime),
)
posts = sa.Table(
    "posts",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("author", None, sa.ForeignKey("users.username")),
    sa.Column("title", sa.String, nullable=False),
    sa.Column("description", sa.String, nullable=False),
)
likes = sa.Table(
    "likes",
    metadata,
    sa.Column("user", None, sa.ForeignKey("users.username")),
    sa.Column("post", None, sa.ForeignKey("posts.id")),
    sa.Column("date", sa.Date, server_default=sa.func.now()),
    sa.UniqueConstraint("user", "post"),
)
metadata.create_all(engine)
