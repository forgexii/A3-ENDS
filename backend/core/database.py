"""
Database Configuration
"""

from sqlalchemy import (
    create_engine
)

from sqlalchemy.orm import (

    declarative_base,

    sessionmaker

)
from backend.core.paths import PROJECT_ROOT

DB_DIR = PROJECT_ROOT / 'backend' / 'data'
DB_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_URL = f"sqlite:///{DB_DIR / 'a3_ends.db'}"


engine = create_engine(

    DATABASE_URL,

    connect_args={

        "check_same_thread":
            False
    }

)

SessionLocal = sessionmaker(

    autocommit=False,

    autoflush=False,

    bind=engine
)

Base = declarative_base()


def get_db():

    db = SessionLocal()

    try:

        yield db

    finally:

        db.close()