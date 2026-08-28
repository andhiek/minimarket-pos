from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.database import get_db

router = APIRouter(prefix="/api/users", tags=["Users"])

@router.get("")
def get_all_users(session: Session = Depends(get_db)):
    # session di sini langsung berupa SQLModel Session
    ...