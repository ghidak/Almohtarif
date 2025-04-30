import random
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, StateFilter
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.client.default import DefaultBotProperties
import asyncio
import os
from dotenv import load_dotenv

# تحميل المتغيرات من ملف .env
load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
CHANNEL_USERNAME = "@almohtarif707"

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

START_POINTS = 2
REFERRAL_POINTS = 1

from datetime import datetime, timedelta

cooldowns = {}  # user_id : time_of_last_request

# ---------------- أدوات مساعدة ---------------- #

def user_exists(user_id):
    with open("users.txt", "r", encoding="utf-8") as f:
        return str(user_id) in f.read()

def get_user_data(user_id):
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

# لجلب بروكسي من ملف proxies_us.txt (العادي)
def get_random_proxy_us():
    with open("proxies_us.txt", "r", encoding="utf-8") as f:
        proxies = [p.strip() for p in f if p.strip()]
        return random.choice(proxies) if proxies else None

# لجلب بروكسي مشفر من ملف proxies.txt
def get_random_proxy_encrypted():
    with open("proxies.txt", "r", encoding="utf-8") as f:
        proxies = [p.strip() for p in f if p.strip()]
        return random.choice(proxies) if proxies else None


def remove_proxy(proxy):
    lines = []
    with open("proxies_us.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()
    with open("proxies_us.txt", "w", encoding="utf-8") as f:
        for line in lines:
            if line.strip() != proxy:
                f.write(line)


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
    kb.button(text="🔐 احصل على بروكسي أمريكي مشفر")
    kb.button(text="🙋‍♂️ اسم المستخدم و ID")
    kb.button(text="❓ شرح الحصول على النقاط")
    return kb.adjust(2).as_markup(resize_keyboard=True)


# ---------------- أوامر المستخدم ---------------- #
@dp.message(F.text == "❓ شرح الحصول على النقاط")
async def how_to_get_points(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 رجوع", callback_data="back_to_menu")]
    ])
    await message.answer(
        "💡 <b>كيف تحصل على نقاط؟</b>\n\n"
        "1️⃣ عند تسجيل كل مستخدم جديد عن طريق <b>رابط الإحالة</b> الخاص بك، تحصل على <b>نقطة مجانية</b>.\n"
        "2️⃣ يتم توزيع نقاط مجانية أحياناً من قِبل الإدارة كمكافآت.\n\n"
        "📢 شارك رابط الإحالة مع أصدقائك لزيادة رصيدك من النقاط واستخدمها للحصول على بروكسيات أمريكية! 🇺🇸",
        reply_markup=keyboard
    )

@dp.callback_query(F.data == "back_to_menu")
async def back_to_main_menu(callback: types.CallbackQuery):
    await callback.message.edit_text("👋 عدت للقائمة الرئيسية.", reply_markup=None)
    await callback.message.answer("اختر من القائمة:", reply_markup=main_menu())


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
    await message.answer(f"💰 نقاطك: {user['points']}\n👥 عدد المحالين: {user['referrals']}")

@dp.message(F.text == "🔗 رابط الإحالة")
async def referral_link(message: Message):
    await message.answer(f"📢 رابط الإحالة الخاص بك:\nhttps://t.me/{(await bot.get_me()).username}?start={message.from_user.id}")

@dp.message(F.text == "🔐 احصل على بروكسي أمريكي مشفر")
async def get_encrypted_proxy(message: Message):
    user_id = message.from_user.id

    now = datetime.now()
    last_request = cooldowns.get(user_id)
    if last_request and now - last_request < timedelta(minutes=1):
        remaining = 60 - (now - last_request).seconds
        return await message.answer(f"⏳ الرجاء الانتظار {remaining} ثانية قبل طلب بروكسي جديد.")
    
    cooldowns[user_id] = now

    if not await is_user_subscribed(user_id):
        return await message.answer(f"⚠️ يجب عليك الاشتراك في القناة أولاً:\n{CHANNEL_USERNAME}")

    user = get_user_data(user_id)
    if user["points"] < 2:
        return await message.answer("❌ تحتاج إلى 2 نقطة للحصول على بروكسي مشفر.")

    searching_message = await message.answer("🔍 <b>جاري البحث عن بروكسي مشفر...</b>\n⏳ الرجاء الانتظار...")

    proxy = None
    for _ in range(10):
       candidate = get_random_proxy_encrypted()

        if candidate and candidate.count(":") == 3 and await is_proxy_working(candidate):
            proxy = candidate
            break
        else:
            if candidate:
                remove_proxy(candidate)

    if not proxy:
        return await searching_message.edit_text("❌ لم يتم العثور على بروكسي مشفر يعمل حالياً.")

    update_user_points(user_id, user["points"] - 2)

    ip, port, usern, passw = proxy.split(":", 3)
    await message.answer(
        f"<b>🔐 بروكسي SOCKS5 مشفر:</b>\n\n"
        f"<b>IP:</b> <code>{ip}</code>\n"
        f"<b>PORT:</b> <code>{port}</code>\n"
        f"<b>Username:</b> <code>{usern}</code>\n"
        f"<b>Password:</b> <code>{passw}</code>\n\n"
        f"🌍 <i>الولايات المتحدة الأمريكية</i>\n"
        f"🎯 <i>تم خصم 2 نقطة - نقاطك المتبقية:</i> <b>{user['points'] - 2}</b>",
        parse_mode=ParseMode.HTML
    )


@dp.message(F.text == "🇺🇸 احصل على بروكسي أمريكي")
async def get_proxy(message: Message):
    user_id = message.from_user.id

    # --- تبريد لمدة دقيقة ---
    now = datetime.now()
    last_request = cooldowns.get(user_id)
    if last_request and now - last_request < timedelta(minutes=1):
        remaining = 60 - (now - last_request).seconds
        return await message.answer(f"⏳ الرجاء الانتظار {remaining} ثانية قبل طلب بروكسي جديد.")
    
    cooldowns[user_id] = now

    if not await is_user_subscribed(user_id):
        return await message.answer(f"⚠️ يجب عليك الاشتراك في القناة أولاً:\n{CHANNEL_USERNAME}")

    user = get_user_data(user_id)
    remaining_points = user["points"]

    if remaining_points < 1:
        return await message.answer(
            f"❌ ليس لديك نقاط كافية. لديك {remaining_points} نقطة فقط. احصل على إحالات لزيادة النقاط."
        )

    searching_message = await message.answer(
        "🔍 <b>جاري البحث عن بروكسي مناسب...</b>\n"
        "🛠️ <i>يتم التحقق من حالة البروكسي...</i>\n"
        "⏳ <i>الرجاء الانتظار قليلاً...</i>"
    )

    # ... يكمل الكود كالمعتاد

    
    cooldowns[user_id] = now


    if not await is_user_subscribed(user_id):
        return await message.answer(f"⚠️ يجب عليك الاشتراك في القناة أولاً:\n{CHANNEL_USERNAME}")

    user = get_user_data(user_id)
    remaining_points = user["points"]

    if remaining_points < 1:
        return await message.answer(
            f"❌ ليس لديك نقاط كافية. لديك {remaining_points} نقطة فقط. احصل على إحالات لزيادة النقاط."
        )

       

    proxy = None
    max_attempts = 10  # عدد المحاولات للعثور على بروكسي شغال
    for _ in range(max_attempts):
        candidate = get_random_proxy()
        if candidate and await is_proxy_working(candidate):
            proxy = candidate
            break
        else:
            if candidate:
                remove_proxy(candidate)

    if not proxy:
        return await message.answer("⚠️ لم يتم العثور على بروكسي شغال حالياً. حاول لاحقاً.")


    # تحديث النقاط بعد الحصول على البروكسي
    update_user_points(user_id, user["points"] - 1)

    # تقسيم البروكسي إلى معلومات منفصلة (نفترض أن البروكسي يحتوي على (IP:PORT:USER:PASS))
    proxy_parts = proxy.split(":", 3)

    if len(proxy_parts) == 4:
        ip, port, username, password = proxy_parts
        formatted_proxy = f"""
    <b>🔌 تم تخصيص بروكسي أمريكي لك!</b>
    <i>إليك التفاصيل:</i>

    <b>IP:</b> <code>{ip}</code>
    <b>PORT:</b> <code>{port}</code>
    <b>Username:</b> <code>{username}</code>
    <b>Password:</b> <code>{password}</code>

    🌍 <i>الموقع:</i> <b>الولايات المتحدة الأمريكية</b>
    🕐 <i>تم التخصيص في:</i> <b>{message.date.strftime('%Y-%m-%d %H:%M:%S')}</b>

    🎉 <i>تم خصم 1 نقطة من رصيدك.</i>
    🔴 <i>نقاطك المتبقية:</i> <b>{user['points'] - 1}</b>
    """
    elif len(proxy_parts) == 2:
        ip, port = proxy_parts
        formatted_proxy = f"""
    <b>🔌 تم تخصيص بروكسي SOCKS5 لك!</b>

    🔹 <b>IP:</b> <code>{ip}</code>  
    🔹 <b>PORT:</b> <code>{port}</code>

    ℹ️ هذا البروكسي لا يحتاج إلى اسم مستخدم أو كلمة مرور — فقط استخدم الـ IP والبورت في إعدادات التطبيق.

    🌍 <i>الموقع:</i> <b>الولايات المتحدة الأمريكية</b>  
    🕐 <i>الوقت:</i> <b>{message.date.strftime('%Y-%m-%d %H:%M:%S')}</b>

    🎉 <i>تم خصم 1 نقطة من رصيدك.</i>  
    🔴 <i>نقاطك المتبقية:</i> <b>{user['points'] - 1}</b>
    """
    else:
        formatted_proxy = "❌ تنسيق البروكسي غير مدعوم حالياً."



    await message.answer(formatted_proxy, parse_mode=ParseMode.HTML)
    await message.answer(
    "🎯 هل تريد المزيد من البروكسيات؟ كل إحالة تكسبك نقطة إضافية!\n"
    "🔗 شارك رابط الإحالة الخاص بك مع أصدقائك وزد رصيدك من النقاط!\n"
    f"https://t.me/{(await bot.get_me()).username}?start={message.from_user.id}"
)



@dp.message(F.text == "🙋‍♂️ اسم المستخدم و ID")
async def user_info(message: Message):
    await message.answer(f"👤 معرفك: @{message.from_user.username}\n🆔 ID: {message.from_user.id}")



# ---------------- لوحة الإدارة ---------------- #

from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove
import re

class AdminStates(StatesGroup):
    waiting_for_proxy_to_add = State()
    waiting_for_proxy_to_remove = State()
    waiting_for_broadcast = State()
    waiting_for_set_points = State()
    waiting_for_gift_all = State()

admin_buttons = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="➕ إضافة بروكسي", callback_data="add_proxy")],
    [InlineKeyboardButton(text="🗑️ حذف بروكسي", callback_data="remove_proxy")],
    [InlineKeyboardButton(text="📢 إرسال رسالة جماعية", callback_data="broadcast")],
    [InlineKeyboardButton(text="✏️ تعديل نقاط مستخدم", callback_data="set_points")],
    [InlineKeyboardButton(text="🎁 إهداء نقاط للجميع", callback_data="gift_all")],
    [InlineKeyboardButton(text="📊 عرض المشتركين", callback_data="view_users")],

    [InlineKeyboardButton(text="📄 عرض البروكسيات", callback_data="available_proxies")]
,
    [InlineKeyboardButton(text="🛑 عرض البروكسيات السيئة", callback_data="bad_proxies")]])

@dp.message(F.text.startswith("/admin"), F.from_user.id == ADMIN_ID)
async def admin_panel(message: Message):
    await message.answer("🛠️ اختر أمراً من لوحة الإدارة:", reply_markup=admin_buttons)

@dp.callback_query(F.data == "add_proxy")
async def handle_add_proxy_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📥 أرسل البروكسي لإضافته (IP:PORT أو IP:PORT:USER:PASS)",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 رجوع", callback_data="admin")]])
    )
    await state.set_state(AdminStates.waiting_for_proxy_to_add)

def format_proxy(proxy: str) -> str:
    return re.sub(r"\s+", "", proxy.strip())

@dp.message(AdminStates.waiting_for_proxy_to_add)
async def process_add_proxy(message: Message, state: FSMContext):
    proxy = format_proxy(message.text)
    with open("proxies.txt", "a", encoding="utf-8") as f:
        f.write(proxy + "\n")
    await message.answer("✅ تم إضافة البروكسي.", reply_markup=ReplyKeyboardRemove())
    await state.clear()

@dp.callback_query(F.data == "remove_proxy")
async def handle_remove_proxy_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🗑️ أرسل البروكسي المراد حذفه.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 رجوع", callback_data="admin")]])
    )
    await state.set_state(AdminStates.waiting_for_proxy_to_remove)

@dp.message(AdminStates.waiting_for_proxy_to_remove)
async def process_remove_proxy(message: Message, state: FSMContext):
    proxy = format_proxy(message.text)
    remove_proxy(proxy)
    await message.answer("🗑️ تم حذف البروكسي.", reply_markup=ReplyKeyboardRemove())
    await state.clear()

@dp.callback_query(F.data == "broadcast")
async def handle_broadcast_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📢 أرسل الرسالة التي تريد إرسالها للجميع.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 رجوع", callback_data="admin")]])
    )
    await state.set_state(AdminStates.waiting_for_broadcast)

@dp.message(AdminStates.waiting_for_broadcast)
async def process_broadcast(message: Message, state: FSMContext):
    with open("users.txt", "r", encoding="utf-8") as f:
        ids = [line.split(":")[0] for line in f]
    for uid in ids:
        try:
            await bot.send_message(uid, message.text)
        except:
            continue
    await message.answer("📢 تم إرسال الرسالة للجميع.", reply_markup=ReplyKeyboardRemove())
    await state.clear()

@dp.callback_query(F.data == "set_points")
async def handle_set_points_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "✏️ أرسل المعرف وعدد النقاط بهذه الصيغة:\n123456789 10",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 رجوع", callback_data="admin")]])
    )
    await state.set_state(AdminStates.waiting_for_set_points)

@dp.message(AdminStates.waiting_for_set_points)
async def process_set_points(message: Message, state: FSMContext):
    try:
        uid, pts = message.text.strip().split()
        update_user_points(int(uid), int(pts))
        await message.answer(f"✅ تم تحديث نقاط المستخدم {uid} إلى {pts}", reply_markup=ReplyKeyboardRemove())
    except:
        await message.answer("❌ الصيغة غير صحيحة. أعد المحاولة.")
    await state.clear()

@dp.callback_query(F.data == "gift_all")
async def handle_gift_all_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🎁 أرسل عدد النقاط التي تريد إهداءها للجميع.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 رجوع", callback_data="admin")]])
    )
    await state.set_state(AdminStates.waiting_for_gift_all)

@dp.message(AdminStates.waiting_for_gift_all)
async def process_gift_all(message: Message, state: FSMContext):
    try:
        # التأكد من أن المدخل هو رقم صحيح
        amount = int(message.text.strip())
        if amount <= 0:
            return await message.answer("❌ يجب أن يكون الرقم أكبر من 0.")

        lines = []
        updated = False  # لمتابعة ما إذا تم تحديث أي بيانات
        with open("users.txt", "r", encoding="utf-8") as f:
            for line in f:
                data = line.strip().split(":")
                if len(data) < 4:
                    continue  # تأكد من أن السطر يحتوي على البيانات الكافية
                data[2] = str(int(data[2]) + amount)  # تحديث النقاط
                lines.append(":".join(data) + "\n")
                updated = True

        if updated:
            with open("users.txt", "w", encoding="utf-8") as f:
                f.writelines(lines)
            await message.answer(f"🎁 تم إهداء {amount} نقطة للجميع.", reply_markup=ReplyKeyboardRemove())
        else:
            await message.answer("❌ لم يتم تحديث أي مستخدمين. تحقق من البيانات.")
    except ValueError:
        # إذا كانت القيمة المدخلة ليست رقماً صحيحاً
        await message.answer("❌ يرجى إرسال رقم صحيح.")
    except Exception as e:
        # في حال حدوث أي خطأ آخر
        await message.answer(f"❌ حدث خطأ غير متوقع: {str(e)}")

    await state.clear()


@dp.callback_query(F.data == "available_proxies")
async def show_available_proxies(callback: types.CallbackQuery):
    try:
        with open("proxies.txt", "r", encoding="utf-8") as f:
            proxies = f.read().strip()
        if not proxies:
            await callback.message.edit_text("📄 لا توجد بروكسيات حالياً.", reply_markup=admin_buttons)
        else:
            formatted = "\n".join([f"🔹 {p}" for p in proxies.splitlines()])
            await callback.message.edit_text(f"📄 قائمة البروكسيات:\n{formatted}", reply_markup=admin_buttons)
    except FileNotFoundError:
        await callback.message.edit_text("📄 ملف البروكسيات غير موجود.", reply_markup=admin_buttons)


@dp.callback_query(F.data == "bad_proxies")
async def show_bad_proxies(callback: types.CallbackQuery):
    try:
        with open("bad_proxies.txt", "r", encoding="utf-8") as f:
            bad = f.read().strip()
        if not bad:
            await callback.message.edit_text("🛑 لا توجد بروكسيات سيئة حالياً.", reply_markup=admin_buttons)
        else:
            formatted = "\n".join([f"❌ {p}" for p in bad.splitlines()])
            await callback.message.edit_text(f"🛑 قائمة البروكسيات السيئة:\n{formatted}", reply_markup=admin_buttons)
    except FileNotFoundError:
        await callback.message.edit_text("🛑 لم يتم العثور على ملف البروكسيات السيئة.", reply_markup=admin_buttons)


@dp.callback_query(F.data == "admin")
async def back_to_admin_panel(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()  # ⬅️ هذه الإضافة مهمة
    await callback.message.edit_text("🛠️ اختر أمراً من لوحة الإدارة:", reply_markup=admin_buttons)


import zipfile
import tempfile

@dp.callback_query(F.data == "view_users")
async def backup_files_zip(callback: types.CallbackQuery):
    files_to_backup = ["proxies.txt", "referrals.txt", "users.txt", "bad_proxies.txt"]
    temp_zip_path = tempfile.gettempdir() + "/backup.zip"

    # إنشاء ملف مضغوط
    with zipfile.ZipFile(temp_zip_path, "w") as backup_zip:
        for file_name in files_to_backup:
            if os.path.exists(file_name):
                backup_zip.write(file_name)

    # التأكد أن الملف المضغوط يحتوي شيئاً
    if os.path.exists(temp_zip_path):
        await bot.send_document(callback.from_user.id, types.FSInputFile(temp_zip_path))
        await callback.answer("✅ تم إرسال النسخة الاحتياطية كملف مضغوط.")
    else:
        await callback.answer("❌ لا توجد ملفات لعمل نسخة احتياطية.", show_alert=True)





async def is_proxy_working(proxy: str) -> bool:
    from aiohttp_socks import ProxyConnector
    import aiohttp

    proxy_parts = proxy.strip().split(":")
    if len(proxy_parts) < 2:
        log_bad_proxy(proxy)
        return False

    ip, port = proxy_parts[0], proxy_parts[1]
    login_pass = ":".join(proxy_parts[2:]) if len(proxy_parts) > 2 else ""

    # نجرب البروكسي مع كل من socks5 و socks4
    for proxy_type in ["socks5", "socks4"]:
        try:
            proxy_url = f"{proxy_type}://{login_pass + '@' if login_pass else ''}{ip}:{port}"
            connector = ProxyConnector.from_url(proxy_url)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get("http://example.com", timeout=5) as response:
                    if response.status == 200:
                        return True
        except Exception:
            continue  # نجرب البروتوكول الآخر

    log_bad_proxy(proxy)
    return False



def log_bad_proxy(proxy: str):
    try:
        with open("bad_proxies.txt", "a", encoding="utf-8") as f:
            f.write(proxy.strip() + "\n")
    except Exception as e:
        print(f"خطأ في تسجيل البروكسي الغير شغال: {e}")





import aiohttp
import asyncio
import os

async def fetch_proxies_periodically():
    url = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=all&timeout=10000&country=us&ssl=all&anonymity=all"
    headers = {"User-Agent": "Mozilla/5.0"}

    while True:
        try:
            existing_proxies = set()
            if os.path.exists("proxies_us.txt"):
                with open("proxies_us.txt", "r", encoding="utf-8") as f:
                    existing_proxies = set(line.strip() for line in f if line.strip())

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        text = await response.text()
                        print("📥 البيانات المستلمة من API:")
                        print(text)

                        proxies = [line.strip() for line in text.splitlines() if line.strip()]
                        new_proxies = [p for p in proxies if p not in existing_proxies]
                        selected = new_proxies[:10]

                        if selected:
                            with open("proxies_us.txt", "a", encoding="utf-8") as f:
                                for proxy in selected:
                                    f.write(proxy + "\n")
                            print(f"✅ تم جلب {len(selected)} بروكسي جديد.")
                        else:
                            print("ℹ️ لا توجد بروكسيات جديدة (كلها مكررة).")
                    else:
                        print(f"⚠️ فشل في جلب البروكسيات. كود الاستجابة: {response.status}")
        except Exception as e:
            print(f"❌ حدث خطأ أثناء جلب البروكسيات: {e}")

        await asyncio.sleep(2 * 60 * 60)  # كل ساعتين



async def main():
    asyncio.create_task(fetch_proxies_periodically())
    print("🤖 البوت يعمل الآن...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
