from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select

from app.database import get_session
from app.users.models import User, UserCreate, UserResponse
from app.auth.utils import hash_password

router = APIRouter(prefix="/api/users", tags=["Users"])

@router.get("", response_model=List[UserResponse])
def get_all_users(session: Session = Depends(get_session)):
    users = session.exec(select(User)).all()
    return users

@router.post("", response_model=UserResponse)
def create_user(user_in: UserCreate, session: Session = Depends(get_session)):
    existing_user = session.exec(select(User).where(User.username == user_in.username)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username sudah digunakan!")

    new_user = User(
        username=user_in.username,
        full_name=user_in.full_name,
        password_hash=hash_password(user_in.password),
        role=user_in.role
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user