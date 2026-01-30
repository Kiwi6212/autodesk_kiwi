from contextlib import contextmanager

from sqlmodel import Session, SQLModel, create_engine

from config import get_settings

settings = get_settings()
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
    echo=settings.debug
)


def init_db() -> None:
    """Initialize database and create all tables."""
    # Import all models to ensure they are registered with SQLModel
    from models import Grade, Task  # noqa: F401
    from auth import User  # noqa: F401

    SQLModel.metadata.create_all(engine)

@contextmanager
def get_session():
    session = Session(engine, expire_on_commit=False)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
