from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models import User, Role
from app.schemas.user import UserCreate,UserLogin,ResetPassword,ChangePassword,UserUpdate
from app.utils.security import hash_password,verify_password
from app.utils.jwt import create_access_token,create_reset_token
from app.utils.dependencies import get_current_user,get_reset_token



router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post("/register", status_code=201)
def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    # Check if email already exists
    existing_user = db.query(User).filter(
        User.email == user_data.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email already registered"
        )

    # Find the default User role
    user_role = db.query(Role).filter(
        Role.name == "User"
    ).first()

    if not user_role:
        raise HTTPException(
            status_code=500,
            detail="Default User role not found"
        )

    # Hash the password
    hashed_password = hash_password(user_data.password)

    # Create new user
    new_user = User(
        name=user_data.name,
        email=user_data.email,
        hashed_password=hashed_password,
        role_id=user_role.id
    )

    # Save user in database
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully",
        "user_id": new_user.id,
        "name": new_user.name,
        "email": new_user.email,
        "role": user_role.name
    }






@router.post("/login")
def login_user(
    user_data: UserLogin,
    db: Session = Depends(get_db)
):
    # Find user by email
    user = db.query(User).filter(
        User.email == user_data.email
    ).first()

    # Check whether user exists
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # Verify password
    if not verify_password(
        user_data.password,
        user.hashed_password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )
    # Check the user is active or not
    if not user.is_active:
        raise HTTPException(
        status_code=403,
        detail="Your account has been deactivated"
    )

    # Generate access token
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "role": user.role.name
        }
    )

    return {
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "bearer"
    }



@router.get("/me")
def get_my_profile(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role.name
    }




@router.post("/forgot-password")
def forgot_password(email: str, db: Session = Depends(get_db)):

    # Find user by email
    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # Generate reset token
    reset_token = create_reset_token(user.id)

    return {
        "message": "Password reset token generated successfully",
        "reset_token": reset_token
    }




@router.post("/reset-password")
def reset_password(
    reset_data: ResetPassword,
    payload : dict = Depends(get_reset_token),
    db: Session = Depends(get_db)
):
    #  Get user ID
    user_id = payload.get("user_id")

    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid reset token"
        )

    #  Find user
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    #  Hash new password
    user.hashed_password = hash_password(reset_data.new_password)

    #  Save changes
    db.commit()

    return {
        "message": "Password reset successful"
    }






@router.post("/change-password")
def change_password(
    password_data: ChangePassword,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify current password
    if not verify_password(
        password_data.current_password,
        current_user.hashed_password
    ):
        raise HTTPException(
            status_code=400,
            detail="Current password is incorrect"
        )

    # Hash the new password
    new_hashed_password = hash_password(password_data.new_password)

    # Update password
    current_user.hashed_password = new_hashed_password

    # Save changes
    db.commit()

    return {
        "message": "Password changed successfully"
    }





@router.post("/logout")
def logout_user(
    current_user: User = Depends(get_current_user)
):
    return {
        "message": "Logout successful"
    }




@router.put("/me")
def update_my_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    current_user.name = user_data.name

    db.commit()
    db.refresh(current_user)

    return {
        "message": "Profile updated successfully",
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role.name
    }