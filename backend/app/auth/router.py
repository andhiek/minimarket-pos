from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
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
    username: str
    password: str


@router.post("/login")
def login(req: LoginRequest, session: Session = Depends(get_db)):
    # 1. Cari pengguna di database berdasarkan username
    user = session.exec(
        select(User).where(User.username == req.username)
    ).first()

    # 2. Jika user tidak ditemukan atau password tidak cocok, lempar HTTP 401
    if not user or not verify_password(req.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username atau password salah!",
        )

    # 3. Kembalikan data profil user jika verifikasi berhasil
    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role,
    }