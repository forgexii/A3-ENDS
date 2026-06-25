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

DATABASE_URL = f"sqlite:///{PROJECT_ROOT / 'backend' / 'data' / 'a3_ends.db'}"


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