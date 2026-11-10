from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session


def database(url: str):
    parsed = make_url(url)
    if parsed.drivername != "sqlite" or not parsed.database or parsed.database == ":memory:":
        raise ValueError("Durable jobs require a file-backed sqlite:/// database")
    Path(parsed.database).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(url, connect_args={"check_same_thread": False, "timeout": 5})

    @event.listens_for(engine, "connect")
    def configure(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=5000")
        connection.execute("PRAGMA journal_mode=WAL")

    return engine


@contextmanager
def write_session(engine):
    # Serialize short writes, including capacity checks and atomic queue claims.
    with Session(engine, expire_on_commit=False) as session:
        session.connection().exec_driver_sql("BEGIN IMMEDIATE")
        try:
            yield session
            session.commit()
        except BaseException:
            session.rollback()
            raise


def require_current_schema(engine):
    from alembic.migration import MigrationContext

    with engine.connect() as connection:
        if MigrationContext.configure(connection).get_current_heads() != ("91f4b02a671c",):
            raise RuntimeError("Run alembic -c backend/alembic.ini upgrade head first")
