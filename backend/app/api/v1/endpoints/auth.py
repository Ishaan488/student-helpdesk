from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.security import create_access_token
from app.models.user import User
from app.schemas.auth import (
    CurrentUserResponse,
    StudentRegister,
    AdminRegister,
    Token,
    UserLogin,
)
from app.services.auth_service import AuthService

router = APIRouter()


@router.post(
    "/token",
    response_model=Token,
    summary="OAuth2 Swagger login (form-data)",
    description="OAuth2 compatible token login for Swagger UI interactive authentication.",
)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    # In OAuth2PasswordRequestForm, username field contains the email
    user = await AuthService.authenticate_user(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role.value}
    )
    return Token(access_token=access_token, token_type="bearer")


@router.post(
    "/login",
    response_model=Token,
    summary="JSON User login",
    description="Standard JSON login for web frontends and mobile clients.",
)
async def login_json(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    user = await AuthService.authenticate_user(
        db, email=credentials.email, password=credentials.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role.value}
    )
    return Token(access_token=access_token, token_type="bearer")


@router.post(
    "/register",
    response_model=CurrentUserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register student account",
    description="Creates a new student account and associated academic profile. (Admin Only)",
)
async def register_student(
    student_data: StudentRegister,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.user import RoleEnum
    if current_user.role not in [RoleEnum.ADMIN, RoleEnum.TPO]:
        raise HTTPException(status_code=403, detail="Not authorized to register users")
        
    user = await AuthService.register_student(db, student_data)
    return user

@router.post(
    "/register-admin",
    response_model=CurrentUserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register admin account",
    description="Creates a new administrator account. (Admin Only)",
)
async def register_admin(
    admin_data: AdminRegister,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.user import RoleEnum
    if current_user.role != RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Only Admins can register new Admins")
        
    user = await AuthService.register_admin(db, admin_data)
    return user


@router.get(
    "/me",
    response_model=CurrentUserResponse,
    summary="Get current user profile",
    description="Returns the profile and role of the currently authenticated user.",
)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user
