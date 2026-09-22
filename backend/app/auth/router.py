from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional
from sqlmodel import Session, select
from passlib.context import CryptContext

from app.database import get_db
from app.models.pos_models import User

router = APIRouter(prefix="/api/auth", tags=["Auth"])

# Context Passlib menggunakan bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


class LoginRequest(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    nik: Optional[str] = Field(default=None, description="NIK kasir untuk login cepat")
    pin: Optional[str] = Field(default=None, description="PIN kasir")


@router.post("/login")
def login(req: LoginRequest, session: Session = Depends(get_db)):
    user = None

    # 1. Logika Login via NIK + PIN (Biasanya untuk Kasir)
    if req.nik and req.pin:
        user = session.exec(
            select(User).where(User.nik == req.nik)
        ).first()
        
        # Validasi PIN (bisa disesuaikan apakah PIN di-hash atau plain text)
        # Jika PIN disimpan plain text di database: user.pin != req.pin
        # Jika PIN di-hash menggunakan bcrypt seperti password: not verify_password(req.pin, user.pin)
        if not user or user.pin != req.pin:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="NIK atau PIN salah!",
            )

    # 2. Logika Login Tradisional via Username + Password (Biasanya untuk Admin)
    elif req.username and req.password:
        user = session.exec(
            select(User).where(User.username == req.username)
        ).first()

        if not user or not verify_password(req.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Username atau password salah!",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Harap masukkan (Username & Password) atau (NIK & PIN)!",
        )

    # Cek apakah user aktif
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akun anda telah dinonaktifkan!",
        )

    # 3. Kembalikan data profil user jika verifikasi berhasil
    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role,
    }
    
