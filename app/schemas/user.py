from pydantic import BaseModel, ConfigDict
from app.models.user import UserRole

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    role: UserRole

class UserResponse(BaseModel):
    id: int
    username: str
    full_name: str
    role: UserRole
    is_active: bool
    model_config = ConfigDict(from_attributes=True)