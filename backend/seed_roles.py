from app.database.connection import SessionLocal
from app.models import Role

db = SessionLocal()

try:
    roles = ["User", "Support Agent", "Admin"]

    for role_name in roles:
        existing_role = db.query(Role).filter(
            Role.name == role_name
        ).first()

        if not existing_role:
            db.add(Role(name=role_name))

    db.commit()

    print("Roles added successfully!")

except Exception as e:
    db.rollback()
    print("Error:", e)

finally:
    db.close()