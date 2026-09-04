import enum
from datetime import datetime
from typing import Optional, ClassVar
from sqlmodel import SQLModel, Field


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    KASIR = "KASIR"


class User(SQLModel, table=True):
    # Menggunakan ClassVar[str] agar Pylance/Pyright tidak komplain type mismatch
    __tablename__: ClassVar[str] = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, nullable=False)
    password_hash: str = Field(nullable=False)
    full_name: str = Field(nullable=False)
    role: str = Field(default="KASIR", nullable=False)
    is_active: bool = Field(default=True, nullable=False)
    created_at: datetime = Field(default_factory=datetime.now)