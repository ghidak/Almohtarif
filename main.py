import random
import os
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.client.default import DefaultBotProperties

from aiohttp_socks import ProxyConnector
import aiohttp

load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
CHANNEL_USERNAME = "@almohtarif707"

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

START_POINTS = 2
REFERRAL_POINTS = 1

# ============== أدوات مساعدة ==============

def user_exists(user_id):
    if not os.path.exists("users.txt"): return False
    with open("users.txt", "r", encoding="utf-8") as f:
        return str(user_id) in f.read()

def save_user(user_id, username, points=2, referrals=0, ref_by=None):
    with open("users.txt", "a", encoding="utf-8") as f:
        line = f"{user_id}:{username}:{points}:{referrals}:{ref_by if ref_by else ''}\n"
        f.write(line)

def get_user_data(user_id):
    if not os.path.exists("users.txt"): return None
    with open("users.txt", "r", encoding="utf-8") as f:
        for line in f:
            data = line.strip().split(":")
            if str(user_id) == data[0]:
                return {"id": data[0], "username": data[1], "points": int(data[2]), "referrals": int(data[3]), "ref_by": data[4] if len(data) > 4 else None}
    return None

def update_user_points(user_id, points):
    lines = []
    with open("users.txt", "r", encoding="utf-8") as f:
        for line in f:
            data = line.strip().split(":")
            if str(user_id) == data[0]:
                data[2] = str(points)
                line = ":".join(data) + "\n"
            lines.append(line)
    with open("users.txt", "w", encoding="utf-8") as f:
        f.writelines(lines)

def increment_referrals(user_id):
    lines = []
    with open("users.txt", "r", encoding="utf-8") as f:
        for line in f:
            data = line.strip().split(":")
            if str(user_id) == data[0]:
                data[3] = str(int(data[3]) + 1)
                line = ":".join(data) + "\n"
            lines.append(line)
    with open("users.txt", "w", encoding="utf-8") as f:
        f.writelines(lines)

def get_random_proxy():
    if not os.path.exists("proxies.txt"): return None
    with open("proxies.txt", "r", encoding="utf-8") as f:
        proxies = [p.strip() for p in f if p.strip()]
        return random.choice(proxies) if proxies else None

def remove_proxy(proxy):
    if not os.path.exists("proxies.txt"): return
    with open("proxies.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()
    with open("proxies.txt", "w", encoding="utf-8") as f:
        for line in lines:
            if line.strip() != proxy:
                f.write(line)

def save_user_proxy(user_id, proxy, timestamp):
    with open("user_proxies.txt", "a", encoding="utf-8") as f:
        f.write(f"{user_id}:{proxy}:{timestamp}\n")

def get_user_proxy(user_id):
    if not os.path.exists("user_proxies.txt"): return None
    with open("user_proxies.txt", "r", encoding="utf-8") as f:
        for line in reversed(f.readlines()):
            parts = line.strip().split(":")
            if str(user_id) == parts[0]:
                proxy = ":".join(parts[1:-1])
                timestamp = parts[-1]
                return proxy, timestamp
    return None

async def is_user_subscribed(user_id):
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

async def is_proxy_working(proxy):
    try:
        parts = proxy.split(":")
        ip, port = parts[0], parts[1]
        login_pass = ":".join(parts[2:]) if len(parts) > 2 else ""

        for proto in ["socks5", "socks4"]:
            proxy_url = f"{proto}://{login_pass + '@' if login_pass else ''}{ip}:{port}"
            connector = ProxyConnector.from_url(proxy_url)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get("http://example.com", timeout=5) as resp:
                    if resp.status == 200:
                        return True
    except:
        pass
    return False

# ============== واجهة المستخدم ==============

def main_menu():
    kb = ReplyKeyboardBuilder()
    kb.button(text="🧾 الحساب")
    kb.button(text="🔗 رابط الإحالة")
    kb.button(text="🇺🇸 احصل على بروكسي أمريكي")
    kb.button(text="🙋‍♂️ اسم المستخدم و ID")
    return kb.adjust(2).as_markup(resize_keyboard=True)

@dp.message(CommandStart())
async def start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or "no_username"

    if not await is_user_subscribed(user_id):
        return await message.answer(f"⚠️ الرجاء الاشتراك أولاً:\n{CHANNEL_USERNAME}")

    if not user_exists(user_id):
        ref_by = None
        if message.text and len(message.text.split()) > 1:
            ref_by = message.text.split()[1]
            if ref_by != str(user_id) and user_exists(ref_by):
                add_points(ref_by, REFERRAL_POINTS)
                increment_referrals(ref_by)
        save_user(user_id, username, START_POINTS, 0, ref_by)

    await message.answer("👋 أهلاً بك في <b>بوت البروكسيات المجانية</b>!", reply_markup=main_menu())

@dp.message(F.text == "🧾 الحساب")
async def account(message: Message):
    user = get_user_data(message.from_user.id)
    await message.answer(f"💰 نقاطك: {user['points']}\n👥 عدد المحالين: {user['referrals']}")

@dp.message(F.text == "🔗 رابط الإحالة")
async def referral(message: Message):
    await message.answer(f"📢 رابط إحالتك:\nhttps://t.me/{(await bot.get_me()).username}?start={message.from_user.id}")

@dp.message(F.text == "🙋‍♂️ اسم المستخدم و ID")
async def user_info(message: Message):
    await message.answer(f"👤 اسمك: @{message.from_user.username}\n🆔 ID: {message.from_user.id}")

@dp.message(F.text == "🇺🇸 احصل على بروكسي أمريكي")
async def get_proxy(message: Message):
    user_id = message.from_user.id

    if not await is_user_subscribed(user_id):
        return await message.answer(f"⚠️ يجب عليك الاشتراك أولاً:\n{CHANNEL_USERNAME}")

    user = get_user_data(user_id)
    if user['points'] < 1:
        return await message.answer("❌ ليس لديك نقاط كافية. اجمع نقاط عبر الإحالات.")

    await message.answer("🔄 جارٍ تجهيز البروكسي لك...")

    proxy = None
    for _ in range(10):
        candidate = get_random_proxy()
        if candidate and await is_proxy_working(candidate):
            proxy = candidate
            break
        elif candidate:
            remove_proxy(candidate)

    if not proxy:
        return await message.answer("⚠️ لا توجد بروكسيات شغالة حالياً.")

    update_user_points(user_id, user["points"] - 1)
    save_user_proxy(user_id, proxy, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))

    proxy_parts = proxy.split(":", 3)
    if len(proxy_parts) == 4:
        ip, port, username, password = proxy_parts
        text = f"<b>🔌 بروكسي جديد:</b>\n\n<b>IP:</b> <code>{ip}</code>\n<b>PORT:</b> <code>{port}</code>\n<b>Username:</b> <code>{username}</code>\n<b>Password:</b> <code>{password}</code>"
    else:
        ip, port = proxy_parts
        text = f"<b>🔌 بروكسي:</b>\n\n<b>IP:</b> <code>{ip}</code>\n<b>PORT:</b> <code>{port}</code>"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="♻️ استبدال البروكسي", callback_data="replace_proxy")]
    ])

    await message.answer(text, reply_markup=kb)

@dp.callback_query(F.data == "replace_proxy")
async def replace_proxy(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = get_user_proxy(user_id)
    if not data:
        return await callback.answer("❌ لا يوجد بروكسي مسجل.", show_alert=True)

    proxy, timestamp = data
    assigned_time = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
    now = datetime.utcnow()

    if now - assigned_time > timedelta(hours=1):
        return await callback.answer("⏰ انتهت مهلة الاستبدال. اطلب بروكسي جديد.", show_alert=True)

    await callback.message.edit_text("🔄 جارٍ تجهيز بروكسي بديل...")

    new_proxy = None
    for _ in range(10):
        candidate = get_random_proxy()
        if candidate and await is_proxy_working(candidate):
            new_proxy = candidate
            break
        elif candidate:
            remove_proxy(candidate)

    if not new_proxy:
        return await callback.message.edit_text("⚠️ لا توجد بروكسيات بديلة حالياً.")

    save_user_proxy(user_id, new_proxy, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))

    proxy_parts = new_proxy.split(":", 3)
    if len(proxy_parts) == 4:
        ip, port, username, password = proxy_parts
        text = f"<b>♻️ بروكسي بديل:</b>\n\n<b>IP:</b> <code>{ip}</code>\n<b>PORT:</b> <code>{port}</code>\n<b>Username:</b> <code>{username}</code>\n<b>Password:</b> <code>{password}</code>"
    else:
        ip, port = proxy_parts
        text = f"<b>♻️ بروكسي بديل:</b>\n\n<b>IP:</b> <code>{ip}</code>\n<b>PORT:</b> <code>{port}</code>"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="♻️ استبدال البروكسي", callback_data="replace_proxy")]
    ])

    await callback.message.edit_text(text, reply_markup=kb)

# ============== تشغيل البوت ==============

async def main():
    print("✅ البوت يعمل الآن ...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
