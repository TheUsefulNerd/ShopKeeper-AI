"""
SQLAlchemy session factory.

Provides the engine and SessionLocal used across the app.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import settings

engine = create_engine(settings.SUPABASE_DB_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
