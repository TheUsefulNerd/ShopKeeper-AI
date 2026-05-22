import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

import app.models.user  # noqa: F401 — ensure all models are registered with Base
from app.models.base import Base
from config import settings

engine = create_engine(settings.SUPABASE_TEST_DB_URL)
TestingSessionLocal = sessionmaker(bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    # The test DB URL sets search_path=test — create the schema if it doesn't exist.
    # Connect without the search_path option so CREATE SCHEMA can run in the public schema.
    plain_url = settings.SUPABASE_TEST_DB_URL.split("?")[0]
    bootstrap_engine = create_engine(plain_url)
    with bootstrap_engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS test"))
        conn.commit()
    bootstrap_engine.dispose()

    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
