import asyncio
from aiogram import Bot, Dispatcher
from os import getenv
from dotenv import load_dotenv
from handlers.routes import router, daily_card
from scripts.fill_subscribes import create_subscribers
from scripts.load_hero import create_tables
from scripts.fill_tarots import fill_tarot


load_dotenv()
TOKEN = getenv('BOT_TOKEN')

dp = Dispatcher()
dp.include_router(router)


async def main():
    bot = Bot(token=TOKEN)
    await create_tables()
    await create_subscribers()
    print('🔄 Заполняем базу данных Таро...')
    await fill_tarot()
    print('✅ База Таро загружена!')
    asyncio.create_task(daily_card(bot))

    print('starting..')


    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())