#!/usr/bin/env python3
"""Database setup script - creates all tables."""

from database.models import Base
from database.connection import engine

def setup_database():
    """Create all database tables."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    setup_database()
