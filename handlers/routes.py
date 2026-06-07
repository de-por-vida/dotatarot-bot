import aiosqlite
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, \
    InlineKeyboardMarkup, CallbackQuery, callback_query, InputMediaPhoto
from datetime import date, datetime
import os
from scripts.fill_subscribes import create_subscribers
import asyncio


router = Router()


# Клавиатура выборов Хелп
def get_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='Посмотреть карту дня'), KeyboardButton(text='Посмотреть свою коллекцию карт')],
            [KeyboardButton(text='Подписаться на ежедневную карту'), KeyboardButton(text='Отписаться от ежедневной карты')]
        ],
        resize_keyboard=True
    )

    return keyboard

# Клаввиатура выборов коллекции
def get_inline():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='📖 Посмотреть всю коллекцию', callback_data='collection_all')],
            [InlineKeyboardButton(text='📜 Посмотреть последние 8 карт коллекции', callback_data='collection_last_8')]
        ]
    )


    return keyboard

# Callback для коллекции

@router.callback_query(F.data.startswith('collection_'))
async def collection_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    action = callback.data

    if action == 'collection_last_8':
        async with aiosqlite.connect('heroes.db') as db:
            async with db.execute("""
                select h.tarot_name, h.localized_name, h.image, udc.date
                from user_daily_cards udc
                join heroes h on udc.hero_id = h.id
                where udc.user_id = ?
                order by udc.date desc
                limit 8
            """, (user_id,)) as cursor:
                cards = await cursor.fetchall()

        if not cards:
            await callback.answer('<b>🃏 Коллекция пока пуста</b>', parse_mode='html')
            return

        media = []
        text = "🃏 <b>Последние 8 карт:</b>\n\n"

        for tarot_name, localized_name, image, card_date in cards:
            photo_path = f'images/heroes/{image}'
            if os.path.exists(photo_path):
                media.append(InputMediaPhoto(media=FSInputFile(photo_path)))
            text += f"• <b>{tarot_name}</b> ({localized_name}) — {card_date}\n"

        if media:
            await callback.message.answer_media_group(media=media)

        await callback.message.answer(text, parse_mode='html')
        await callback.answer()

    elif action == 'collection_all':
        user_id = callback.from_user.id

        async with aiosqlite.connect('heroes.db') as db:
            async with db.execute("""
            SELECT h.tarot_name, h.localized_name, udc.date
            FROM user_daily_cards udc
            JOIN heroes h ON udc.hero_id = h.id
            WHERE udc.user_id = ?
            ORDER BY udc.date DESC
            """, (user_id,)) as cursor:
                cards1 = await cursor.fetchall()


        if not cards1:
            await callback.answer('<b>🃏 Коллекция пока пуста</b>', parse_mode='html')
            return

        text = '🃏 <b>Твоя коллекция карт:</b>\n\n'
        for tarot_name, hero_name, date in cards1:
            text += f'• <b>{tarot_name}</b> ({hero_name}) — {date}\n'

        await callback.message.answer(text, parse_mode='html')


# Работа с подписчиками

async def add_subscriber(user_id):
    async with aiosqlite.connect('heroes.db') as db:
        await db.execute("""
           insert or ignore into subscribers (user_id) values (?)""", (user_id,))
        await db.commit()

async def get_subscribers():
    async with (aiosqlite.connect('heroes.db') as db):
        async with db.execute('select * from subscribers') as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

async def remove_subscriber(user_id):
    async with aiosqlite.connect('heroes.db') as db:
        await db.execute('DELETE FROM subscribers WHERE user_id = ?', (user_id,))
        await db.commit()



# Daily tarot Рассылка

async def send_tarot_card(bot: Bot, user_id: int):
    today = date.today().isoformat()
    async with aiosqlite.connect('heroes.db') as db:
        async with db.execute("""
                   SELECT id, localized_name, tarot_name, prediction, advice, image 
                   FROM heroes 
                   WHERE tarot_name IS NOT NULL 
                   ORDER BY RANDOM() 
                   LIMIT 1
               """) as cursor:
            hero_data = await cursor.fetchone()

        if not hero_data:
            return

        hero_id = hero_data[0]

        await db.execute("""
            INSERT INTO user_daily_cards (user_id, hero_id, date)
            VALUES (?, ?, ?)
        """, (user_id, hero_id, today))
        await db.commit()

    localized_name, tarot_name, prediction, advice, image = hero_data[1:]

    text = (
        f"🃏 <b>Карта дня </b>✨\n\n"
        f"<b>{tarot_name}</b>\n"
        f"<i>{localized_name}</i>\n\n"
        f"{prediction}\n\n"
        f"📌 <b>Интересный факт:</b>\n{advice}"
    )

    photo_path = f'images/heroes/{image}'

    if os.path.exists(photo_path):
        await bot.send_photo(chat_id=user_id, photo=FSInputFile(photo_path), caption=text, parse_mode='html')
    else:
        await bot.send_message(chat_id=user_id, text=text, parse_mode='html')


# Рассылка сообщений

async def daily_card(bot: Bot):
    while True:
        now = datetime.now()
        if now.hour == 0 and now.minute == 0:
            subscribers = await get_subscribers()
            for user_id in subscribers:
                try:
                    await send_tarot_card(bot, user_id)
                except Exception:
                    pass
        await asyncio.sleep(60)


# Стартовая команда, для запуска бота

@router.message(Command('start'))
async def start(message: Message):
    await message.answer(
        f'<b>Привет, {message.from_user.full_name}!</b> Бот, который каждый день (или по запросу) вытягивает тебе одного случайного героя Доты в формате карт Таро.\n'
        'Каждая карта несёт предсказание, интересный факт и атмосферное описание в формате карт таро.\n'
        '<b>Это смесь гороскопа, мотивации и полезной игровой инфы.</b>', parse_mode='html'
    )


# Команда, которая выводит список команд для бота

@router.message(Command('help'))
async def help(message: Message):
    await message.answer(
        '<b>Вот список команд, доступных в этом боте:</b>\n\n'
        '<b>/tarot</b> - с помощью этой команды можно вытянуть карту.\n'
        '<b>/daily</b> - подписка на ежедневную карту.\n'
        '<b>/undaily</b> - отписаться от ежедневной рассылки.\n'
        '<b>/collection</b> - список карт, которые тебе уже выпадали.\n', parse_mode='html',
        reply_markup=get_keyboard()
    )


# Команда, которая выдает карту
@router.message(Command('tarot'))
@router.message(F.text == 'Посмотреть карту дня'.strip())
async def tarot(message: Message):
    user_id = message.from_user.id
    today = date.today().isoformat()

    async with aiosqlite.connect('heroes.db') as db:
        async with db.execute("""
            SELECT h.localized_name, h.tarot_name, h.prediction, h.advice, h.image
            FROM user_daily_cards udc
            JOIN heroes h ON udc.hero_id = h.id
            WHERE udc.user_id = ? AND udc.date = ?
        """, (user_id, today)) as cursor:
            hero = await cursor.fetchone()

        if hero:
            localized_name, tarot_name, prediction, advice, image = hero
            text = (
                f"🃏 <b>Карта дня </b>✨\n\n"
                f"<b>{tarot_name}</b>\n"
                f"<i>{localized_name}</i>\n\n"
                f"{prediction}\n\n"
                f"📌 <b>Интересный факт:</b>\n{advice}"
            )
        else:
            async with db.execute("""
                SELECT id, localized_name, tarot_name, prediction, advice, image 
                FROM heroes 
                WHERE tarot_name IS NOT NULL 
                ORDER BY RANDOM() 
                LIMIT 1
            """) as cursor:
                hero_data = await cursor.fetchone()

            if not hero_data:
                await message.answer('База данных пуста!')
                return

            hero_id = hero_data[0]
            localized_name, tarot_name, prediction, advice, image = hero_data[1:]

            await db.execute("""
                INSERT INTO user_daily_cards (user_id, hero_id, date)
                VALUES (?, ?, ?)
            """, (user_id, hero_id, today))
            await db.commit()

            text = (
                f"🃏 <b>Карта дня </b>✨\n\n"
                f"<b>{tarot_name}</b>\n"
                f"<i>{localized_name}</i>\n\n"
                f"{prediction}\n\n"
                f"📌 <b>Интересный факт:</b>\n{advice}"
            )

    photo_path = f'images/heroes/{image}'

    if os.path.exists(photo_path):
        await message.answer_photo(
            photo=FSInputFile(photo_path),
            caption=text,
            parse_mode='html'
        )
    else:
        await message.answer(text + "\n\n⚠️ Изображение недоступно", parse_mode='html')

# Подписка на отправку карты каждый день

@router.message(Command('daily'))
@router.message(F.text == 'Подписаться на ежедневную карту'.strip())
async def daily(message: Message):
    user_id = message.from_user.id

    await add_subscriber(user_id)
    await message.answer('Вы успешно подписались на ежедневную отправку карты!')


# Отписка от отправки карты каждый день

@router.message(Command('undaily'))
@router.message(F.text == 'Отписаться от ежедневной карты'.strip())
async def unsub_daily(message: Message):
    user_id = message.from_user.id

    await remove_subscriber(user_id)
    await message.answer('Вы успешно отписались от ежедневной карты!')



# Карты, которые тебе уже выпадали

@router.message(Command('collection'))
@router.message(F.text == 'Посмотреть свою коллекцию карт'.strip())
async def collection(message: Message):
    user_id = message.from_user.id
    async with aiosqlite.connect('heroes.db') as db:
        async with db.execute("""
            SELECT COUNT(*) FROM user_daily_cards WHERE user_id = ?
        """, (user_id,)) as cursor:
            total_row = await cursor.fetchone()
            total = total_row[0] if total_row else 0


    if total == 0:
        await message.answer(
            '🃏 <b>У тебя пока нет карт!</b> 🃏\n\n'
            'Напиши /tarot чтобы начать собирать ✨',
            parse_mode='html'
        )
        return





    text = (f'🃏 <b>Твоя коллекция карт - {total}/127 карт</b>\n\n')

    keabord = get_inline()

    await message.answer(text, parse_mode='html', reply_markup=keabord)

