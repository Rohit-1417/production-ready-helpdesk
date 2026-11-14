from app.database.connection import Base, engine
from app.models import Role, User, Ticket

Base.metadata.create_all(bind=engine)

print("Tables created successfully!")