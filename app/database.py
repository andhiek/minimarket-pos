from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlmodel import SQLModel, Session
from app.config import settings

# Engine setup (Menyesuaikan SQLite vs PostgreSQL)
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL, 
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency injection untuk Session SQLAlchemy / SQLModel"""
    with Session(engine) as session:
        yield session

# Alias get_session ke get_db agar kompatibel dengan import get_session
get_session = get_db

def create_db_and_tables():
    """Membuat tabel otomatis untuk semua model SQLModel"""
    SQLModel.metadata.create_all(engine)