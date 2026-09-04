from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from pydantic import BaseModel, ConfigDict
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.auth.utils import verify_password  # Menggunakan utility verifikasi password

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    full_name: Optional[str] = None
    role: str

    model_config = ConfigDict(from_attributes=True)

@router.post("/login", response_model=UserResponse)
def login(data: LoginRequest, session: Session = Depends(get_db)):
    # Cari user berdasarkan username
    user = session.exec(select(User).where(User.username == data.username)).first()
    
    # Ganti dengan komparasi plain text langsung
    if not user or user.password_hash != data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username atau password salah!"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akun Anda tidak aktif!"
        )

    return UserResponse.model_validate(user)