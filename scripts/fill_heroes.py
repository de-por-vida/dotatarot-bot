import aiosqlite
import asyncio
import aiohttp


async def fill_heroes():
    async with aiohttp.ClientSession() as session:
        async with session.get('https://api.opendota.com/api/heroes') as resp:
            data = await resp.json()
    async with aiosqlite.connect('heroes.db') as db:
        for hero in data:
            image_name = hero['name'].replace('npc_dota_hero_', '') + '.jpg'
            await db.execute("""
                INSERT OR IGNORE INTO heroes 
                (id, name, localized_name, primary_attr, attack_type, roles, image)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                hero['id'], hero['name'], hero['localized_name'],
                hero.get('primary_attr'), hero.get('attack_type'),
                str(hero.get('roles', [])), image_name
            ))
        await db.commit()
        print(f'✅ Загружено {len(data)} героев')
