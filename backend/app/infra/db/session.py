"""Database engine factory. The schema lives in the `dm` schema (alembic migration 0001)."""

from sqlalchemy import Engine, create_engine

from app.config.settings import get_settings


def make_engine(url: str | None = None) -> Engine:
    url = url or get_settings().database_url
    if not url:
        raise RuntimeError("DATABASE_URL is not set (see backend/.env.example)")
    # search_path so that unqualified table and function names resolve to the dm schema
    return create_engine(
        url, connect_args={"options": "-c search_path=dm,public"}, pool_pre_ping=True
    )
