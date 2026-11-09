from fastapi import APIRouter, Depends , HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models import User,Role
from app.schemas.user import UserRoleUpdate,UserStatusUpdate
from app.utils.dependencies import get_current_admin

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users")
def get_all_users(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    users = db.query(User).all()

    return [
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role.name
        }
        for user in users
    ]



@router.get("/users/{user_id}")
def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role.name
    }




@router.put("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    role_data: UserRoleUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin)
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    role = db.query(Role).filter(Role.id == role_data.role_id).first()

    if not role:
        raise HTTPException(
            status_code=404,
            detail="Role not found"
        )

    user.role_id = role.id

    db.commit()
    db.refresh(user)

    return {
        "message": "User role updated successfully",
        "user_id": user.id,
        "name": user.name,
        "new_role": role.name
    }





@router.put("/users/{user_id}/status")
def update_user_status(
    user_id: int,
    status_data: UserStatusUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if user.id == current_admin.id and not status_data.is_active:
        raise HTTPException(
            status_code=400,
            detail="Admin cannot deactivate their own account"
        )

    user.is_active = status_data.is_active

    db.commit()
    db.refresh(user)

    return {
        "message": "User status updated successfully",
        "user_id": user.id,
        "name": user.name,
        "is_active": user.is_active
    }