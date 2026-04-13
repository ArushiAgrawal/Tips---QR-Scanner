from database import SessionLocal, engine
from models import Base, User

# Create tables
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Check users
print("=== USERS ===")
users = db.query(User).all()
if users:
    for user in users:
        print(user)
        # print(f"ID: {user.id}, Phone: {user.phone_number}, UPI: {user.upi_id}, Status: {user.status}, Created: {user.created_at}")
else:
    print("No users found")

db.close()
print("\n✓ Database check complete")