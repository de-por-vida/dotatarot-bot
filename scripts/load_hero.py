import asyncio
import aiosqlite



async def create_tables():
    async with aiosqlite.connect('heroes.db') as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS heroes (
                id INTEGER PRIMARY KEY,
                name TEXT,
                localized_name TEXT,
                primary_attr TEXT,
                attack_type TEXT,
                roles TEXT,
                image TEXT,
                tarot_name TEXT,
                prediction TEXT,
                advice TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_daily_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                hero_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                UNIQUE (user_id, date)
             )
        """)
        await db.commit()
        print('✅ Таблицы созданы')


if __name__ == '__main__':
    asyncio.run(create_tables())
