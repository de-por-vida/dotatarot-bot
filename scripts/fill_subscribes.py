import asyncio
import aiosqlite

async def create_subscribers():
    async with aiosqlite.connect('heroes.db') as db:
        await db.execute("""
                         create table if not exists subscribers (
                         user_id INTEGER primary key)
        """
        )
        await db.commit()