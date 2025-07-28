from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import timedelta, datetime
from typing import Dict, Any
import uuid
import logging

from app.models.auth_models import UserSignupRequest, UserLoginRequest, TokenResponse, UserResponse, UserRole
from app.auth_utils import verify_password, get_password_hash, create_access_token, verify_token, ACCESS_TOKEN_EXPIRE_MINUTES
from app.firebase_config import get_ref

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()

# Mock users for testing - these remain for backward compatibility
MOCK_USERS = [
    {
        "id": "admin-1",
        "email": "admin@hospital.com",
        "name": "Dr. Sarah Johnson",
        "role": "admin",
        "department": "Administration",
        "password_hash": get_password_hash("password")
    },
    {
        "id": "doctor-1", 
        "email": "doctor@hospital.com",
        "name": "Dr. Michael Chen",
        "role": "doctor",
        "department": "Cardiology",
        "specialization": "Interventional Cardiology",
        "password_hash": get_password_hash("password")
    },
    {
        "id": "staff-1",
        "email": "staff@hospital.com", 
        "name": "Emma Wilson",
        "role": "staff",
        "department": "ICU",
        "specialization": "Critical Care Nursing",
        "password_hash": get_password_hash("password")
    }
]

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get current authenticated user from JWT token"""
    try:
        payload = verify_token(credentials.credentials)
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        # Try to get user from Firebase first
        users_ref = get_ref('users')
        users_data = users_ref.get() or {}
        
        for uid, user_data in users_data.items():
            if uid == user_id:
                return {"id": uid, **user_data}
        
        # Fallback to mock users for testing
        for user in MOCK_USERS:
            if user["id"] == user_id:
                return user
                
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

@router.post("/signup", response_model=TokenResponse)
async def signup(user_data: UserSignupRequest):
    """Register a new user"""
    try:
        # Check if user already exists
        users_ref = get_ref('users')
        users_data = users_ref.get() or {}
        
        # Check in Firebase users
        for uid, existing_user in users_data.items():
            if existing_user.get('email') == user_data.email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this email already exists"
                )
        
        # Check in mock users too
        for existing_user in MOCK_USERS:
            if existing_user['email'] == user_data.email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this email already exists"
                )
        
        # Create new user
        user_id = str(uuid.uuid4())
        hashed_password = get_password_hash(user_data.password)
        
        new_user = {
            "email": user_data.email,
            "first_name": user_data.first_name,
            "last_name": user_data.last_name,
            "role": user_data.role.value,
            "department": user_data.department,
            "specialization": user_data.specialization,
            "password_hash": hashed_password,
            "created_at": str(datetime.utcnow()),
            "is_active": True
        }
        
        # Save to Firebase
        user_ref = get_ref(f'users/{user_id}')
        user_ref.set(new_user)
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user_id, "email": user_data.email, "role": user_data.role.value},
            expires_delta=access_token_expires
        )
        
        # Create response user object
        response_user = UserResponse(
            id=user_id,
            email=user_data.email,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            role=user_data.role.value,
            department=user_data.department,
            specialization=user_data.specialization,
            created_at=new_user["created_at"]
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=response_user
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please check your information and try again."
        )

@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLoginRequest):
    """Authenticate user and return access token"""
    try:
        # First check Firebase users
        users_ref = get_ref('users')
        users_data = users_ref.get() or {}
        
        user_found = None
        user_id = None
        
        # Check Firebase users
        for uid, user_data in users_data.items():
            if user_data.get('email') == login_data.email:
                if verify_password(login_data.password, user_data.get('password_hash', '')):
                    user_found = user_data
                    user_id = uid
                    break
        
        # Fallback to mock users for testing
        if not user_found:
            for user in MOCK_USERS:
                if user['email'] == login_data.email:
                    if verify_password(login_data.password, user['password_hash']):
                        user_found = user
                        user_id = user['id']
                        break
        
        if not user_found:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user_id, "email": user_found['email'], "role": user_found['role']},
            expires_delta=access_token_expires
        )
        
        # Create response user object
        if 'first_name' in user_found and 'last_name' in user_found:
            # New format with first_name and last_name
            response_user = UserResponse(
                id=user_id,
                email=user_found['email'],
                first_name=user_found['first_name'],
                last_name=user_found['last_name'],
                role=user_found['role'],
                department=user_found.get('department'),
                specialization=user_found.get('specialization'),
                created_at=user_found.get('created_at', '')
            )
        else:
            # Legacy format with name field (for mock users)
            name_parts = user_found.get('name', '').split(' ', 1)
            first_name = name_parts[0] if name_parts else ''
            last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            response_user = UserResponse(
                id=user_id,
                email=user_found['email'],
                first_name=first_name,
                last_name=last_name,
                role=user_found['role'],
                department=user_found.get('department'),
                specialization=user_found.get('specialization'),
                created_at=user_found.get('created_at', '')
            )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=response_user
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please check your credentials and try again."
        )

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current user information"""
    # Handle both new format (first_name, last_name) and legacy format (name)
    if 'first_name' in current_user and 'last_name' in current_user:
        return UserResponse(
            id=current_user['id'],
            email=current_user['email'],
            first_name=current_user['first_name'],
            last_name=current_user['last_name'],
            role=current_user['role'],
            department=current_user.get('department'),
            specialization=current_user.get('specialization'),
            created_at=current_user.get('created_at', '')
        )
    else:
        # Legacy format - split name field
        name_parts = current_user.get('name', '').split(' ', 1)
        first_name = name_parts[0] if name_parts else ''
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        return UserResponse(
            id=current_user['id'],
            email=current_user['email'],
            first_name=first_name,
            last_name=last_name,
            role=current_user['role'],
            department=current_user.get('department'),
            specialization=current_user.get('specialization'),
            created_at=current_user.get('created_at', '')
        )

@router.post("/logout")
async def logout():
    """Logout user (client should discard the token)"""
    return {"message": "Successfully logged out"}
