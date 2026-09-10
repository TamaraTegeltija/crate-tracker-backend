import os

from sqlalchemy import create_engine, URL
from sqlalchemy.orm import sessionmaker, declarative_base


# Podaci za konekciju se uzimaju iz environment variables.
db_url = URL.create(
    drivername="postgresql+psycopg2",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", "5432")),
    database=os.getenv("DB_NAME")
)


# Engine predstavlja konekciju SQLAlchemy-ja prema bazi.
engine = create_engine(db_url)


# SessionLocal pravi nove database session objekte.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


Base = declarative_base()


def get_db():

    # Pravimo jednu sesiju prema bazi.
    db = SessionLocal()

    try:
        # FastAPI endpoint ce koristiti ovu sesiju.
        yield db

    finally:
        # Kada se request zavrsi,
        # obavezno zatvaramo sesiju.
        db.close()