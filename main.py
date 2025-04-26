import random
import time
from keep_alive import keep_alive
keep_alive()
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, StateFilter
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove
import aiohttp
import asyncio
import os
import re
from dotenv import load_dotenv
from aiohttp_socks import ProxyConnector

# تحميل المتغيرات من ملف .env
load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
CHANNEL_USERNAME = "@almohtarif707"

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

START_POINTS = 2
REFERRAL_POINTS = 1

# تبريد طلبات البروكسي
cooldowns = {}
# تبريد طلبات الاستبدال
swap_cooldowns = {}

# رسائل الانتظار العشوائية
WAIT_MESSAGES = [
    "🔍 جاري البحث عن أفضل بروكسي لك...",
    "⏳ انتظر قليلاً، يتم تجهيز البروكسي...",
    "🛠️ يتم التحقق من جودة البروكسي...",
    "📡 يتم الآن اختيار أسرع بروكسي متاح..."
]
# ---------------- أدوات مساعدة ---------------- #

def user_exists(user_id):
    if not os.path.exists("users.txt"):
        return False
    with open("users.txt", "r", encoding="utf-8") as f:
        return str(user_id) in f.read()

def get_user_data(user_id):
    if not os.path.exists("users.txt"):
        return None
    with open("users.txt", "r", encoding="utf-8") as f:
        for line in f:
            data = line.strip().split(":")
            if str(user_id) == data[0]:
                return {
                    "id": data[0],
                    "username": data[1],
                    "points": int(data[2]),
                    "referrals": int(data[3]),
                    "ref_by": data[4] if len(data) > 4 else None
                }
    return None

def save_user(user_id, username, points=2, referrals=0, ref_by=None):
    with open("users.txt", "a", encoding="utf-8") as f:
        line = f"{user_id}:{username}:{points}:{referrals}:{ref_by if ref_by else ''}\n"
        f.write(line)

def update_user_points(user_id, new_points):
    if not os.path.exists("users.txt"):
        return
    lines = []
    with open("users.txt", "r", encoding="utf-8") as f:
        for line in f:
            data = line.strip().split(":")
            if str(user_id) == data[0]:
                data[2] = str(new_points)
                line = ":".join(data) + "\n"
            lines.append(line)
    with open("users.txt", "w", encoding="utf-8") as f:
        f.writelines(lines)

def increment_referrals(user_id):
    if not os.path.exists("users.txt"):
        return
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

def add_points(user_id, amount):
    user = get_user_data(user_id)
    if user:
        update_user_points(user_id, user["points"] + amount)

def get_random_proxy():
    if not os.path.exists("proxies.txt"):
        return None
    with open("proxies.txt", "r", encoding="utf-8") as f:
        proxies = [p.strip() for p in f if p.strip()]
        return random.choice(proxies) if proxies else None

def remove_proxy(proxy):
    if not os.path.exists("proxies.txt"):
        return
    lines = []
    with open("proxies.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()
    with open("proxies.txt", "w", encoding="utf-8") as f:
        for line in lines:
            if line.strip() != proxy:
                f.write(line)

def log_bad_proxy(proxy: str):
    try:
        with open("bad_proxies.txt", "a", encoding="utf-8") as f:
            f.write(proxy.strip() + "\\n")
    except Exception as e:
        print(f"خطأ في تسجيل البروكسي الغير شغال: {e}")
# ---------------- التحقق من الاشتراك ---------------- #

async def is_user_subscribed(user_id):
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# ---------------- الواجهة ---------------- #

def main_menu():
    kb = ReplyKeyboardBuilder()
    kb.button(text="🧾 الحساب")
    kb.button(text="🔗 رابط الإحالة")
    kb.button(text="🇺🇸 احصل على بروكسي أمريكي")
    kb.button(text="🔄 استبدال بروكسي")
    kb.button(text="🙋‍♂️ اسم المستخدم و ID")
    return kb.adjust(2).as_markup(resize_keyboard=True)

# ---------------- أوامر المستخدم ---------------- #

@dp.message(CommandStart())
async def start_cmd(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or "no_username"

    if not await is_user_subscribed(user_id):
        return await message.answer(f"⚠️ الرجاء الاشتراك في القناة أولاً:\n{CHANNEL_USERNAME}")

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
async def account_info(message: Message):
    user = get_user_data(message.from_user.id)
    await message.answer(f"💰 نقاطك: <b>{user['points']}</b>\n👥 عدد المحالين: <b>{user['referrals']}</b>")

@dp.message(F.text == "🔗 رابط الإحالة")
async def referral_link(message: Message):
    await message.answer(f"📢 رابط الإحالة الخاص بك:\nhttps://t.me/{(await bot.get_me()).username}?start={message.from_user.id}")

@dp.message(F.text == "🙋‍♂️ اسم المستخدم و ID")
async def user_info(message: Message):
    await message.answer(f"👤 معرفك: @{message.from_user.username}\n🆔 ID: {message.from_user.id}")
async def is_proxy_working(proxy: str) -> bool:
    proxy_parts = proxy.strip().split(":")
    if len(proxy_parts) < 2:
        log_bad_proxy(proxy)
        return False

    ip, port = proxy_parts[0], proxy_parts[1]
    login_pass = ":".join(proxy_parts[2:]) if len(proxy_parts) > 2 else ""

    for proxy_type in ["socks5", "socks4"]:
        try:
            proxy_url = f"{proxy_type}://{login_pass + '@' if login_pass else ''}{ip}:{port}"
            connector = ProxyConnector.from_url(proxy_url)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get("http://example.com", timeout=5) as response:
                    if response.status == 200:
                        return True
        except:
            continue
    log_bad_proxy(proxy)
    return False

@dp.message(F.text == "🇺🇸 احصل على بروكسي أمريكي")
async def get_proxy(message: Message):
    user_id = message.from_user.id
    now = time.time()

    if not await is_user_subscribed(user_id):
        return await message.answer(f"⚠️ يجب عليك الاشتراك في القناة أولاً:\n{CHANNEL_USERNAME}")

    if user_id in cooldowns and now - cooldowns[user_id] < 60:
        wait_sec = int(60 - (now - cooldowns[user_id]))
        return await message.answer(f"⏳ يرجى الانتظار {wait_sec} ثانية قبل طلب بروكسي جديد.")

    user = get_user_data(user_id)
    if not user or user["points"] < 1:
        return await message.answer(f"❌ ليس لديك نقاط كافية.\n💳 نقاطك الحالية: {user['points'] if user else 0}")

    cooldowns[user_id] = now

    await message.answer(random.choice(WAIT_MESSAGES))
    await asyncio.sleep(3)

    proxy = None
    for _ in range(10):
        candidate = get_random_proxy()
        if candidate and await is_proxy_working(candidate):
            proxy = candidate
            break
        else:
            if candidate:
                remove_proxy(candidate)

    if not proxy:
        return await message.answer("⚠️ لم يتم العثور على بروكسي شغال حالياً. حاول لاحقاً.")

    update_user_points(user_id, user["points"] - 1)

    parts = proxy.split(":")
    if len(parts) == 4:
        ip, port, username, password = parts
        text = f"""
<b>🔌 بروكسي أمريكي SOCKS5 مميز!</b>

<b>IP:</b> <code>{ip}</code>
<b>PORT:</b> <code>{port}</code>
<b>Username:</b> <code>{username}</code>
<b>Password:</b> <code>{password}</code>

🎯 صالح للاستخدام الفوري!
🎉 تم خصم 1 نقطة من حسابك.
"""
    elif len(parts) == 2:
        ip, port = parts
        text = f"""
<b>🔌 بروكسي SOCKS5 بدون حساب!</b>

<b>IP:</b> <code>{ip}</code>
<b>PORT:</b> <code>{port}</code>

🎯 يمكنك استخدامه مباشرة!
🎉 تم خصم 1 نقطة من حسابك.
"""
    else:
        text = "❌ خطأ في تنسيق البروكسي."

    await message.answer(text)

@dp.message(F.text == "🔄 استبدال بروكسي")
async def swap_proxy(message: Message):
    user_id = message.from_user.id
    now = time.time()

    if user_id in swap_cooldowns and now - swap_cooldowns[user_id] < 3600:
        wait_min = int((3600 - (now - swap_cooldowns[user_id])) / 60)
        return await message.answer(f"🔄 يمكنك استبدال البروكسي بعد {wait_min} دقيقة.")

    swap_cooldowns[user_id] = now

    await get_proxy(message)
# ---------------- لوحة الإدارة ---------------- #

admin_buttons = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="➕ إضافة بروكسي", callback_data="add_proxy")],
    [InlineKeyboardButton(text="🗑️ حذف بروكسي", callback_data="remove_proxy")],
    [InlineKeyboardButton(text="📢 إرسال رسالة جماعية", callback_data="broadcast")],
    [InlineKeyboardButton(text="✏️ تعديل نقاط مستخدم", callback_data="set_points")],
    [InlineKeyboardButton(text="🎁 إهداء نقاط للجميع", callback_data="gift_all")],
    [InlineKeyboardButton(text="👥 عرض عدد المستخدمين", callback_data="show_users")],
    [InlineKeyboardButton(text="🧹 تنظيف البروكسيات السيئة", callback_data="clean_bad_proxies")]
])

class AdminStates(StatesGroup):
    waiting_for_proxy_to_add = State()
    waiting_for_proxy_to_remove = State()
    waiting_for_broadcast = State()
    waiting_for_set_points = State()
    waiting_for_gift_all = State()

@dp.message(F.text.startswith("/admin"), F.from_user.id == ADMIN_ID)
async def admin_panel(message: Message):
    await message.answer("🛠️ لوحة الإدارة:", reply_markup=admin_buttons)

@dp.callback_query(F.data == "add_proxy")
async def handle_add_proxy_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("📥 أرسل البروكسي لإضافته:", reply_markup=back_admin_button())
    await state.set_state(AdminStates.waiting_for_proxy_to_add)

@dp.message(AdminStates.waiting_for_proxy_to_add)
async def process_add_proxy(message: Message, state: FSMContext):
    proxy = message.text.strip()
    with open("proxies.txt", "a", encoding="utf-8") as f:
        f.write(proxy + "\\n")
    await message.answer("✅ تم إضافة البروكسي.", reply_markup=ReplyKeyboardRemove())
    await state.clear()

@dp.callback_query(F.data == "remove_proxy")
async def handle_remove_proxy_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("🗑️ أرسل البروكسي المراد حذفه:", reply_markup=back_admin_button())
    await state.set_state(AdminStates.waiting_for_proxy_to_remove)

@dp.message(AdminStates.waiting_for_proxy_to_remove)
async def process_remove_proxy(message: Message, state: FSMContext):
    proxy = message.text.strip()
    remove_proxy(proxy)
    await message.answer("🗑️ تم حذف البروكسي.", reply_markup=ReplyKeyboardRemove())
    await state.clear()

@dp.callback_query(F.data == "broadcast")
async def handle_broadcast_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("📢 أرسل الرسالة لإرسالها لجميع المستخدمين:", reply_markup=back_admin_button())
    await state.set_state(AdminStates.waiting_for_broadcast)

@dp.message(AdminStates.waiting_for_broadcast)
async def process_broadcast(message: Message, state: FSMContext):
    if not os.path.exists("users.txt"):
        return await message.answer("❌ لا يوجد مستخدمين.")
    with open("users.txt", "r", encoding="utf-8") as f:
        ids = [line.split(":")[0] for line in f]
    for uid in ids:
        try:
            await bot.send_message(uid, message.text)
        except:
            continue
    await message.answer("✅ تم إرسال الرسالة للجميع.", reply_markup=ReplyKeyboardRemove())
    await state.clear()

@dp.callback_query(F.data == "set_points")
async def handle_set_points_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("✏️ أرسل المعرف وعدد النقاط (مثال: 123456789 10):", reply_markup=back_admin_button())
    await state.set_state(AdminStates.waiting_for_set_points)

@dp.message(AdminStates.waiting_for_set_points)
async def process_set_points(message: Message, state: FSMContext):
    try:
        uid, pts = message.text.strip().split()
        update_user_points(uid, int(pts))
        await message.answer(f"✅ تم تحديث نقاط المستخدم {uid} إلى {pts}.", reply_markup=ReplyKeyboardRemove())
    except:
        await message.answer("❌ خطأ في الصيغة.")
    await state.clear()

@dp.callback_query(F.data == "gift_all")
async def handle_gift_all_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("🎁 أرسل عدد النقاط لإهدائها للجميع:", reply_markup=back_admin_button())
    await state.set_state(AdminStates.waiting_for_gift_all)

@dp.message(AdminStates.waiting_for_gift_all)
async def process_gift_all(message: Message, state: FSMContext):
    try:
        amount = int(message.text.strip())
        lines = []
        with open("users.txt", "r", encoding="utf-8") as f:
            for line in f:
                data = line.strip().split(":")
                if len(data) >= 4:
                    data[2] = str(int(data[2]) + amount)
                    lines.append(":".join(data) + "\\n")
        with open("users.txt", "w", encoding="utf-8") as f:
            f.writelines(lines)
        await message.answer(f"🎁 تم إهداء {amount} نقطة لجميع المستخدمين.", reply_markup=ReplyKeyboardRemove())
    except:
        await message.answer("❌ حدث خطأ.")
    await state.clear()

@dp.callback_query(F.data == "show_users")
async def show_users(callback: types.CallbackQuery):
    if not os.path.exists("users.txt"):
        return await callback.message.edit_text("لا يوجد مستخدمين.")
    with open("users.txt", "r", encoding="utf-8") as f:
        users = f.readlines()
    await callback.message.edit_text(f"👥 عدد المستخدمين المسجلين: <b>{len(users)}</b>", reply_markup=admin_buttons)

@dp.callback_query(F.data == "clean_bad_proxies")
async def clean_bad_proxies(callback: types.CallbackQuery):
    if os.path.exists("bad_proxies.txt"):
        os.remove("bad_proxies.txt")
    await callback.message.edit_text("🧹 تم تنظيف ملف البروكسيات السيئة.", reply_markup=admin_buttons)

def back_admin_button():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 رجوع", callback_data="admin")]
    ])

@dp.callback_query(F.data == "admin")
async def back_to_admin(callback: types.CallbackQuery):
    await callback.message.edit_text("🛠️ لوحة الإدارة:", reply_markup=admin_buttons)

# ---------------- تشغيل البوت ---------------- #

async def main():
    print("🤖 البوت يعمل...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
