
import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from database import (
    init_db,
    user_exists,
    save_user,
    get_user_data,
    update_user_points,
    add_points,
    increment_referrals,
    get_all_user_ids,
    gift_all_users
)

load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
CHANNEL_USERNAME = "@almohtarif707"

bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

START_POINTS = 2
REFERRAL_POINTS = 1
COOLDOWN_SECONDS = 30
user_cooldowns = {}

def main_menu():
    kb = ReplyKeyboardBuilder()
    kb.button(text="🧾 الحساب")
    kb.button(text="🔗 رابط الإحالة")
    kb.button(text="🇺🇸 احصل على بروكسي أمريكي")
    kb.button(text="🙋‍♂️ اسم المستخدم و ID")
    return kb.adjust(2).as_markup(resize_keyboard=True)

async def is_user_subscribed(user_id):
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

@dp.message(CommandStart())
async def start_cmd(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or "no_username"

    if not await is_user_subscribed(user_id):
        return await message.answer(f"⚠️ الرجاء الاشتراك في القناة أولاً:
{CHANNEL_USERNAME}")

    if not user_exists(user_id):
        ref_by = None
        if message.text and len(message.text.split()) > 1:
            ref_by = message.text.split()[1]
            if ref_by != str(user_id) and user_exists(int(ref_by)):
                add_points(int(ref_by), REFERRAL_POINTS)
                increment_referrals(int(ref_by))
        save_user(user_id, username, START_POINTS, 0, ref_by)

    await message.answer("👋 أهلاً بك في <b>بوت البروكسيات المجانية</b>!", reply_markup=main_menu())

@dp.message(F.text == "🧾 الحساب")
async def account_info(message: Message):
    user = get_user_data(message.from_user.id)
    await message.answer(f"💰 نقاطك: {user['points']}
👥 عدد المحالين: {user['referrals']}")

@dp.message(F.text == "🔗 رابط الإحالة")
async def referral_link(message: Message):
    await message.answer(f"📢 رابط الإحالة الخاص بك:
https://t.me/{(await bot.get_me()).username}?start={message.from_user.id}")

@dp.message(F.text == "🙋‍♂️ اسم المستخدم و ID")
async def user_info(message: Message):
    await message.answer(f"👤 معرفك: @{message.from_user.username}
🆔 ID: {message.from_user.id}")

def get_random_proxy():
    if not os.path.exists("proxies.txt"):
        return None
    with open("proxies.txt", "r", encoding="utf-8") as f:
        proxies = [p.strip() for p in f if p.strip()]
    return proxies[0] if proxies else None

@dp.message(F.text == "🇺🇸 احصل على بروكسي أمريكي")
async def get_proxy(message: Message):
    user_id = message.from_user.id

    if not await is_user_subscribed(user_id):
        return await message.answer(f"⚠️ يجب عليك الاشتراك في القناة أولاً:
{CHANNEL_USERNAME}")

    now = datetime.now()
    last_time = user_cooldowns.get(user_id)
    if last_time and (now - last_time).total_seconds() < COOLDOWN_SECONDS:
        remaining = int(COOLDOWN_SECONDS - (now - last_time).total_seconds())
        return await message.answer(f"🕒 الرجاء الانتظار {remaining} ثانية قبل طلب بروكسي جديد.")
    user_cooldowns[user_id] = now

    user = get_user_data(user_id)
    if user['points'] < 1:
        return await message.answer("❌ ليس لديك نقاط كافية. احصل على إحالات لزيادة النقاط.")

    proxy = get_random_proxy()
    if not proxy:
        return await message.answer("⚠️ لا توجد بروكسيات متاحة حالياً.")

    update_user_points(user_id, user['points'] - 1)
    await message.answer(f"🔌 بروكسي: <code>{proxy}</code>\n🟢 تم خصم 1 نقطة من رصيدك.", parse_mode=ParseMode.HTML)

async def main():
    init_db()
    print("🤖 البوت يعمل الآن...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
