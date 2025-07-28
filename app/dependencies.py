from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.auth_utils import verify_token, validate_role
from app.firebase_config import get_ref
from app.models.auth_models import TokenData
from typing import Optional

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Get current user from JWT token"""
    try:
        # Verify the token
        payload = verify_token(credentials.credentials)
        email = payload.get("sub")
        role = payload.get("role")
        
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        
        # Get user from Firebase
        users_ref = get_ref('users')
        users_data = users_ref.get()
        
        if not users_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Find user by email
        user_data = None
        user_id = None
        for uid, user in users_data.items():
            if user.get('email') == email:
                user_data = user
                user_id = uid
                break
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return {
            "id": user_id,
            "email": user_data.get("email"),
            "role": user_data.get("role"),
            "first_name": user_data.get("first_name"),
            "last_name": user_data.get("last_name"),
            "phone": user_data.get("phone"),
            "department": user_data.get("department"),
            "specialization": user_data.get("specialization"),
            "created_at": user_data.get("created_at")
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

def require_role(required_role: str):
    """Dependency factory to require specific role"""
    async def role_checker(current_user: dict = Depends(get_current_user)):
        if not validate_role(required_role, current_user["role"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. {required_role.title()} role or higher required."
            )
        return current_user
    return role_checker

# Pre-defined role dependencies
async def require_admin(current_user: dict = Depends(get_current_user)):
    """Require admin role"""
    if not validate_role("admin", current_user["role"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin role required."
        )
    return current_user

async def require_doctor(current_user: dict = Depends(get_current_user)):
    """Require doctor role or higher"""
    if not validate_role("doctor", current_user["role"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Doctor role or higher required."
        )
    return current_user

async def require_staff(current_user: dict = Depends(get_current_user)):
    """Require staff role or higher (any authenticated user)"""
    if not validate_role("staff", current_user["role"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Staff role or higher required."
        )
    return current_user
