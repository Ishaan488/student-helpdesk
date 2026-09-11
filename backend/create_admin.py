import asyncio
from app.core.database import SessionLocal
from app.models.user import User, RoleEnum
from app.core.security import get_password_hash

async def create_admin():
    async with SessionLocal() as db:
        # Check if admin already exists
        admin_email = "admin@college.edu"
        
        # We need to manually do a select
        from sqlalchemy import select
        res = await db.execute(select(User).where(User.email == admin_email))
        existing_admin = res.scalar_one_or_none()
        
        if existing_admin:
            print(f"Admin {admin_email} already exists!")
            return

        print("Creating admin account...")
        new_admin = User(
            email=admin_email,
            hashed_password=get_password_hash("admin123"),
            full_name="System Admin",
            role=RoleEnum.ADMIN,
            is_active=True
        )
        db.add(new_admin)
        await db.commit()
        print(f"Successfully created admin account: {admin_email} with password: admin123")

if __name__ == "__main__":
    asyncio.run(create_admin())
