from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from enum import Enum

class UserRole(str, Enum):
    STAFF = "staff"
    DOCTOR = "doctor"
    ADMIN = "admin"

class UserSignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    role: UserRole
    phone: Optional[str] = None
    department: Optional[str] = None
    specialization: Optional[str] = None

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    role: str
    phone: Optional[str] = None
    department: Optional[str] = None
    specialization: Optional[str] = None
    created_at: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
