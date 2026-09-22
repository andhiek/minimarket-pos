from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from app.models.user import UserRole

class LoginRequest(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    nik: Optional[str] = Field(default=None, description="NIK kasir untuk login cepat")
    pin: Optional[str] = Field(default=None, description="PIN 4-6 digit kasir")

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    full_name: str
    role: UserRole

class UserCreate(BaseModel):
    nik: Optional[str] = None
    username: str
    password: str
    pin: Optional[str] = Field(default=None, max_length=6, description="PIN angka untuk kasir")
    full_name: str
    role: UserRole = UserRole.KASIR

class UserResponse(BaseModel):
    id: int
    nik: Optional[str] = None
    username: str
    full_name: str
    role: UserRole
    is_active: bool
    model_config = ConfigDict(from_attributes=True)