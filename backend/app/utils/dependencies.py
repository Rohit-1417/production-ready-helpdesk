from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models import User
from app.utils.jwt import verify_token

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials

    # Step 1: Verify JWT
    payload = verify_token(token)

    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    # Step 2: Reject password-reset tokens
    if payload.get("type") == "password_reset":
        raise HTTPException(
            status_code=401,
            detail="Password reset token cannot be used for this route"
        )

    # Step 3: Get user ID from token
    user_id = payload.get("sub")

    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid token payload"
        )

    # Step 4: Find user in database
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Invalid token payload"
        )

    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    # Step 5: Check the user is active or not
    if not user.is_active:
        raise HTTPException(
        status_code=403,
        detail="Your account has been deactivated"
    )

    return user




def get_reset_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    payload = verify_token(token)

    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired reset token"
        )

    if payload.get("type") != "password_reset":
        raise HTTPException(
            status_code=401,
            detail="Password reset token required"
        )

    return payload





def get_current_admin(current_user: User = Depends(get_current_user)):
    if current_user.role.name != "Admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    return current_user




def get_current_agent(current_user: User = Depends(get_current_user)):
    if current_user.role.name != "Support Agent":
        raise HTTPException(
            status_code=403,
            detail="Support Agent access required"
        )

    return current_user