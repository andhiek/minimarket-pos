from enum import Enum
from typing import Optional
from sqlmodel import Field, SQLModel

class UserRole(str, Enum):
    ADMIN = "admin"
    CASHIER = "kasir"

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    full_name: str
    password_hash: str
    role: UserRole = Field(default=UserRole.CASHIER)
    is_active: bool = Field(default=True)

class UserCreate(SQLModel):
    username: str
    full_name: str
    password: str
    role: UserRole = UserRole.CASHIER

class UserResponse(SQLModel):
    id: int
    username: str
    full_name: str
    role: UserRole
    is_active: bool