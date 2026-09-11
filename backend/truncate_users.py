import asyncio
from sqlalchemy import text
from app.core.database import async_session_factory

async def truncate_users():
    async with async_session_factory() as db:
        await db.execute(text("TRUNCATE TABLE users CASCADE;"))
        await db.commit()
        print("Successfully wiped users and students tables.")

if __name__ == "__main__":
    asyncio.run(truncate_users())
