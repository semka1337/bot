import asyncio
import os
import sys
import time
import json
from datetime import datetime, timedelta
from aiogram.types import FSInputFile
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# Импорт Rich компонентов
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.progress import track
except ImportError:
    print("❌ Ошибка: Библиотека 'rich' не найдена. Установи её: pip install rich")
    sys.exit(1)

console = Console()

# ================= НАСТРОЙКИ (МЕНЯЙ ТУТ) =================
# Используем переменную окружения или хардкод (лучше использовать Secrets)
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8224789408:AAG96abOF5jwrP9dyytGA5VpF2XBSzWxYPI")
OWNER_ID = 8318103039  # ID покупателя (Гл. Админ)
DEV_ID = 8352711680    # ТВОЙ ID (Разработчик)

LINKS = {
    "chat": "https://t.me/+1q9l4w1cpvs1MTVi",
    "main_group": "https://t.me/+pnJcW7Mvw1UwMzBi",
    "manual_seller": "@Volshebnik1SPLIT",
    "rach_seller": "@Apim091 | @X_A_ML"
}

DB_USERS = "users_base.txt"
MODS_FILE = "mods.txt"
BANNED_USERS_FILE = "banned_users.json"  # Файл для хранения забаненных пользователей
# =========================================================

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

class States(StatesGroup):
    waiting_for_issue = State()
    waiting_for_broadcast = State()
    waiting_for_reply = State()
    adding_mod = State()
    ban_user = State()

pending_tickets = {}

# --- РАБОТА С БАНОМ ---
def load_banned_users():
    """Загружает список забаненных пользователей из файла"""
    if not os.path.exists(BANNED_USERS_FILE):
        return {}
    
    try:
        with open(BANNED_USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_banned_users(banned_users):
    """Сохраняет список забаненных пользователей в файл"""
    with open(BANNED_USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(banned_users, f, ensure_ascii=False, indent=2)

def is_user_banned(user_id):
    """Проверяет, забанен ли пользователь"""
    banned_users = load_banned_users()
    user_str = str(user_id)
    
    if user_str in banned_users:
        ban_info = banned_users[user_str]
        ban_until = datetime.fromisoformat(ban_info['until'])
        
        # Если время бана истекло, удаляем пользователя из списка
        if datetime.now() > ban_until:
            del banned_users[user_str]
            save_banned_users(banned_users)
            return False
        return True
    return False

def ban_user(user_id, duration_hours, banned_by_name, reason=""):
    """Банит пользователя на указанное количество часов"""
    banned_users = load_banned_users()
    
    ban_until = datetime.now() + timedelta(hours=duration_hours)
    
    banned_users[str(user_id)] = {
        'until': ban_until.isoformat(),
        'banned_by': banned_by_name,
        'reason': reason,
        'banned_at': datetime.now().isoformat(),
        'duration_hours': duration_hours
    }
    
    save_banned_users(banned_users)
    return ban_until

def unban_user(user_id):
    """Разбанивает пользователя"""
    banned_users = load_banned_users()
    user_str = str(user_id)
    
    if user_str in banned_users:
        del banned_users[user_str]
        save_banned_users(banned_users)
        return True
    return False

def get_ban_info(user_id):
    """Получает информацию о бане пользователя"""
    banned_users = load_banned_users()
    user_str = str(user_id)
    
    if user_str in banned_users:
        ban_info = banned_users[user_str]
        ban_until = datetime.fromisoformat(ban_info['until'])
        
        # Если время бана истекло, удаляем
        if datetime.now() > ban_until:
            del banned_users[user_str]
            save_banned_users(banned_users)
            return None
        
        return ban_info
    return None

# --- ВИЗУАЛ КОНСОЛИ ---
def startup_visual():
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # 1. Ахуевший баннер
    banner = Text(r"""
    
      █▀▀█ █▀▀ █▀▀█ █▀▀▄ █▀▀ █▀▄▀█ █──█    █▀▀ █▀▀█ █── ░█▀▀█ ▀▀█▀▀ 
      █▄▄█ █── █▄▄█ █──█ █▀▀ █─▀─█ █▄▄█    ▀▀█ █──█ █── ░█▄▄█ ──█── 
      ▀──▀ ▀▀▀ ▀──▀ ▀▀▀─ ▀▀▀ ▀───▀ ▄▄▄█    ▀▀▀ █▀▀▀ ▀▀▀ ░█─── ──▀──
    """, style="bold magenta")
    
    console.print(Panel(banner, subtitle="[bold red]REPLIT EDITION[/bold red]", border_style="bright_blue"))

    # 2. Таблица состояния
    table = Table(show_header=True, header_style="bold cyan", border_style="bright_black")
    table.add_column("COMPONENT", style="dim", width=20)
    table.add_column("STATUS", justify="center")
    table.add_column("DETAILS", justify="right")

    table.add_row("Core Engine", "[bold green]READY[/bold green]", "v3.14 (Unlocked)")
    table.add_row("Security Layer", "[bold green]BYPASSED[/bold green]", "Replit")
    table.add_row("License Key", "[bold green]UNLIMITED[/bold green]", "Free Access")
    table.add_row("API Gateway", "[bold green]CONNECTED[/bold green]", "Telegram API")
    table.add_row("Ban System", "[bold green]ACTIVE[/bold green]", "Time-based")

    console.print(table)
    print("\n")

    console.print(f"\n[bold white on green] SUCCESS [/bold white on green] [bold white]Бот успешно запущен на Replit. Добро пожаловать, Босс.[/bold white]\n")

def is_admin(user_id):
    """Проверяет, является ли пользователь главным админом"""
    return user_id in [OWNER_ID, DEV_ID]  # И OWNER_ID и DEV_ID имеют права админа

def is_moderator(user_id):
    """Проверяет, является ли пользователь модератором"""
    if is_admin(user_id):  # Админы тоже имеют доступ к тикетам
        return True
    if not os.path.exists(MODS_FILE): 
        return False
    with open(MODS_FILE, "r") as f:
        return str(user_id) in f.read().splitlines()

def save_user(user_id):
    if not os.path.exists(DB_USERS): open(DB_USERS, "w").close()
    with open(DB_USERS, "a+") as f:
        f.seek(0)
        if str(user_id) not in f.read(): f.write(f"{user_id}\n")

# --- КЛАВИАТУРЫ ---
def main_kb():
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="⚡️ ВОРВАТЬСЯ В АКАДЕМИЮ", url=LINKS["chat"]))
    kb.row(InlineKeyboardButton(text="💎 ПРАЙС-ЛИСТ", callback_data="show_price"),
           InlineKeyboardButton(text="👑 КАНАЛ", url=LINKS["main_group"]))
    kb.row(InlineKeyboardButton(text="🆘 ПОДДЕРЖКА / КУПИТЬ", callback_data="support_req"))
    return kb.as_markup()

def admin_menu_kb():
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="📩 ТИКЕТЫ (ПОДДЕРЖКА)", callback_data="adm_tickets"))
    kb.row(InlineKeyboardButton(text="📢 РАССЫЛКА", callback_data="adm_broadcast"))
    kb.row(InlineKeyboardButton(text="👤 МОДЕРЫ", callback_data="adm_mods"))
    kb.row(InlineKeyboardButton(text="⛔️ БАН СИСТЕМА", callback_data="adm_bans"))
    return kb.as_markup()

def moder_menu_kb():
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="📩 ТИКЕТЫ (ПОДДЕРЖКА)", callback_data="mod_tickets"))
    kb.row(InlineKeyboardButton(text="⬅️ НАЗАД", callback_data="mod_back"))
    return kb.as_markup()

def ban_options_kb(user_id):
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="⏳ 1 час", callback_data=f"ban_{user_id}_1"),
        InlineKeyboardButton(text="⏳ 6 часов", callback_data=f"ban_{user_id}_6")
    )
    kb.row(
        InlineKeyboardButton(text="⏳ 12 часов", callback_data=f"ban_{user_id}_12"),
        InlineKeyboardButton(text="⏳ 24 часа", callback_data=f"ban_{user_id}_24")
    )
    kb.row(
        InlineKeyboardButton(text="⏳ 3 дня", callback_data=f"ban_{user_id}_72"),
        InlineKeyboardButton(text="⏳ 7 дней", callback_data=f"ban_{user_id}_168")
    )
    kb.row(
        InlineKeyboardButton(text="⏳ 30 дней", callback_data=f"ban_{user_id}_720"),
        InlineKeyboardButton(text="🚫 Навсегда", callback_data=f"ban_{user_id}_perm")
    )
    kb.row(InlineKeyboardButton(text="❌ Отмена", callback_data=f"cancel_ban_{user_id}"))
    return kb.as_markup()

def ban_management_kb():
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="📋 СПИСОК ЗАБАНЕННЫХ", callback_data="list_banned"))
    kb.row(InlineKeyboardButton(text="⬅️ НАЗАД", callback_data="adm_back"))
    return kb.as_markup()

def price_kb():
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="🧰 РАСХОДНИКИ", callback_data="consumables"),
        InlineKeyboardButton(text="⬅️ НАЗАД", callback_data="back_to_main")
    )
    return kb.as_markup()

def consumables_kb():
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="⬅️ К МАНУАЛАМ", callback_data="show_price"))
    return kb.as_markup()

# --- ХЕНДЛЕРЫ ЮЗЕРОВ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    save_user(message.from_user.id)
    user_name = message.from_user.first_name.upper() if message.from_user.first_name else "АБУЗЕР"
    now = datetime.now().strftime("%H:%M — %d.%m.%y")

    text = (
        f"<b>ДОБРО ПОЖАЛОВАТЬ В ЭЛИТУ, {user_name}!</b> ⚡️\n"
        f"<code>————————————————————————————</code>\n"
        f"Ты в <b>ACADEMY SPLIT</b>. Здесь не место нытикам и теоретикам. "
        f"Мы не учим жизни, мы учим выжимать из системы миллионы, пока она спит.\n\n"
        f"🚀 <b>ТВОЙ ЗАРЯЖЕННЫЙ АРСЕНАЛ:</b>\n"
        f"🔹 <b>Manuals:</b> Приватные мануалы, которые не сливают.\n"
        f"🔹 <b>Supply:</b> Аккаунты и верифы, которые не летят во фрод.\n"
        f"🔹 <b>Support:</b> Модеры-хищники, готовые помочь 24/7.\n\n"
        f"<i>Либо ты забираешь банк сегодня, либо завтра это сделает другой. Твой выбор.</i>\n"
        f"<code>————————————————————————————</code>\n"
        f"🛰 <b>STATUS:</b> <code>STABLE</code> | <b>ACCESS:</b> <code>GRANTED</code>\n"
        f"📅 <b>UPTIME:</b> <code>{now}</code>"
    )
    await message.answer(text=text, reply_markup=main_kb())

@dp.callback_query(F.data == "show_price")
async def send_price(call: types.CallbackQuery):
    try:
        # Пытаемся отправить картинку с текстом
        photo = FSInputFile("price.jpg")
        price_text = (
            f"<b>⚔️ ТВОЙ АРСЕНАЛ ДЛЯ РАБОТЫ ПО КРУПНОМУ ⚔️</b>\n\n"
            f"Хватит гадать и тыкаться вслепую. Мы выкатываем ультимативные решения, которые кормят профи и оставляют конкурентов глотать пыль.\n\n"
            f"<b>ВЫБИРАЙ СВОЙ КАЛИБР:</b>\n\n"
            f"<b>🌟 АССАСИН — 5000₽</b>\n"
            f"Высшая ступень. Быстрый, незаметный, смертоносный для профита. Схема, которая обходит любые преграды.\n\n"
            f"<b>🛡 ТИТАН — 3500₽</b>\n"
            f"Непробиваемая классика. Бетонная надежность и стабильный доход. Твой фундамент в этом деле.\n\n"
            f"<b>⚒️ МОЛОТ — 3000₽</b>\n"
            f"Грубая сила и мощь. Пробиваем темы там, где другие пасуют. Инструмент для тех, кто берет своё силой.\n\n"
            f"<b>🟣 ВБ (Wildberries) — 3000₽</b>\n"
            f"Твой личный код доступа к маркетплейсу. Все фишки, обходы и секреты в одном пакете.\n\n"
            f"<code>————————————————————————————</code>\n"
            f"⚠️ <b>ЗНАНИЯ — ЭТО ЕДИНСТВЕННАЯ ВАЛЮТА, КОТОРАЯ НЕ ОБЕСЦЕНИВАЕТСЯ.</b>\n\n"
            f"<b>{LINKS['manual_seller']} 🚀</b> — Залетай сейчас и начинай еб*шить рынок. Завтра будешь жалеть, что не купил сегодня."
        )
        
        await call.message.answer_photo(
            photo=photo,
            caption=price_text,
            reply_markup=price_kb()
        )
        await call.message.delete()
    except Exception as e:
        # Если картинки нет, отправляем просто текст
        price_text = (
            f"<b>⚔️ ТВОЙ АРСЕНАЛ ДЛЯ РАБОТЫ ПО КРУПНОМУ ⚔️</b>\n\n"
            f"Хватит гадать и тыкаться вслепую. Мы выкатываем ультимативные решения, которые кормят профи и оставляют конкурентов глотать пыль.\n\n"
            f"<b>ВЫБИРАЙ СВОЙ КАЛИБР:</b>\n\n"
            f"<b>🌟 АССАСИН — 5000₽</b>\n"
            f"Высшая ступень. Быстрый, незаметный, смертоносный для профита. Схема, которая обходит любые преграды.\n\n"
            f"<b>🛡 ТИТАН — 3500₽</b>\n"
            f"Непробиваемая классика. Бетонная надежность и стабильный доход. Твой фундамент в этом деле.\n\n"
            f"<b>⚒️ МОЛОТ — 3000₽</b>\n"
            f"Грубая сила и мощь. Пробиваем темы там, где другие пасуют. Инструмент для тех, кто берет своё силой.\n\n"
            f"<b>🟣 ВБ (Wildberries) — 3000₽</b>\n"
            f"Твой личный код доступа к маркетплейсу. Все фишки, обходы и секреты в одном пакете.\n\n"
            f"<code>————————————————————————————</code>\n"
            f"⚠️ <b>ЗНАНИЯ — ЭТО ЕДИНСТВЕННАЯ ВАЛЮТА, КОТОРАЯ НЕ ОБЕСЦЕНИВАЕТСЯ.</b>\n\n"
            f"<b>{LINKS['manual_seller']} 🚀</b> — Залетай сейчас и начинай еб*шить рынок. Завтра будешь жалеть, что не купил сегодня."
        )
        await call.message.answer(text=price_text, reply_markup=price_kb())

@dp.callback_query(F.data == "consumables")
async def show_consumables(call: types.CallbackQuery):
    text = (
        f"<b>⚡️ МЫ: ТВОЙ ДОСТУП В ИГРУ ⚡️</b>\n\n"
        f"Пока остальные обещают — мы делаем. Самый сочный прайс на рынке, без лишнего мусора и задержек.\n\n"
        
        f"☘️ <b>SIM-АКТИВАЦИЯ:</b> Запускаем твою связь за <code>12$</code>. Моментально. Анонимно.\n\n"
        
        f"✅ <b>VERIF PAY/WB:</b> Верификация под ключ — <code>2000₽</code>. Чистый проход, залетает со свистом.\n\n"
        
        f"🔥 <b>ГОСУСЛУГИ:</b> Полный доступ — <code>45$</code>. Для тех, кто решает серьезные задачи.\n\n"
        
        f"🏦 <b>АЛЬФА БАНК:</b> Финансовая база за <code>25$</code>. Стабильнее, чем швейцарские часы.\n\n"
        
        f"<b>💎 КАЧЕСТВО — БЕТОН. СКОРОСТЬ — ПУЛЯ.</b>\n\n"

        f"<i>⚡️ {LINKS['rach_seller']} — Пиши по факту. Работаем быстро, лишних вопросов не задаем. Кто успел — тот и в дамках.</i>\n"
    )
    
    try:
        # Убедись что картинка есть в папке с ботом и называется "consumables.jpg"
        photo = FSInputFile("consumables.jpg")
        await call.message.answer_photo(
            photo=photo,
            caption=text,
            reply_markup=consumables_kb()
        )
        await call.message.delete()
    except:
        # Если картинки нет, отправим просто текст
        await call.message.answer(text=text, reply_markup=consumables_kb())

@dp.callback_query(F.data == "back_to_main")
async def back_to_main(call: types.CallbackQuery):
    await call.message.delete()
    await cmd_start(call.message)

# --- ТЕХПОДДЕРЖКА ---
@dp.callback_query(F.data == "support_req")
async def sup_req(call: types.CallbackQuery, state: FSMContext):
    # Проверяем, не забанен ли пользователь
    if is_user_banned(call.from_user.id):
        ban_info = get_ban_info(call.from_user.id)
        if ban_info:
            ban_until = datetime.fromisoformat(ban_info['until'])
            time_left = ban_until - datetime.now()
            hours_left = int(time_left.total_seconds() // 3600)
            minutes_left = int((time_left.total_seconds() % 3600) // 60)
            
            await call.message.answer(
                f"⛔️ <b>ДОСТУП К ПОДДЕРЖКЕ ЗАБЛОКИРОВАН</b>\n\n"
                f"<b>Причина:</b> {ban_info.get('reason', 'Не указана')}\n"
                f"<b>Заблокировал:</b> {ban_info['banned_by']}\n"
                f"<b>Разблокировка через:</b> {hours_left}ч {minutes_left}м\n\n"
                f"<i>Ожидайте разблокировки или обратитесь напрямую.</i>"
            )
            return
    
    await call.message.answer("📝 <b>Напиши свой вопрос:</b>")
    await state.set_state(States.waiting_for_issue)

@dp.message(States.waiting_for_issue)
async def sup_save(message: types.Message, state: FSMContext):
    # Проверяем, не забанен ли пользователь
    if is_user_banned(message.from_user.id):
        ban_info = get_ban_info(message.from_user.id)
        if ban_info:
            ban_until = datetime.fromisoformat(ban_info['until'])
            time_left = ban_until - datetime.now()
            hours_left = int(time_left.total_seconds() // 3600)
            minutes_left = int((time_left.total_seconds() % 3600) // 60)
            
            await message.answer(
                f"⛔️ <b>ВЫ ЗАБАНЕНЫ!</b>\n\n"
                f"Ваше сообщение не было отправлено в поддержку.\n"
                f"<b>Причина:</b> {ban_info.get('reason', 'Не указана')}\n"
                f"<b>Заблокировал:</b> {ban_info['banned_by']}\n"
                f"<b>Разблокировка через:</b> {hours_left}ч {minutes_left}м"
            )
            await state.clear()
            return
    
    uid = message.from_user.id
    pending_tickets[uid] = {
        "text": message.text, 
        "user": message.from_user.first_name,
        "username": message.from_user.username or "Нет username",
        "user_id": uid
    }
    await message.answer("✅ <b>Отправлено!</b>\nМодератор ответит вам в ближайшее время.")
    
    # Отправляем уведомление админам и модераторам
    staff_ids = [OWNER_ID, DEV_ID]  # Оба админа
    if os.path.exists(MODS_FILE):
        with open(MODS_FILE, "r") as f:
            staff_ids.extend([int(line.strip()) for line in f if line.strip()])
    
    notification_text = (
        f"🔔 <b>НОВЫЙ ТИКЕТ #{len(pending_tickets)}</b>\n\n"
        f"👤 <b>Пользователь:</b> {message.from_user.first_name}\n"
        f"🆔 <b>ID:</b> <code>{uid}</code>\n"
        f"📝 <b>Сообщение:</b>\n<code>{message.text[:200]}...</code>\n\n"
        f"📊 <b>Активных тикетов:</b> {len(pending_tickets)}\n"
        f"👉 <code>/moder</code>"
    )
    
    for staff_id in set(staff_ids):
        try:
            await bot.send_message(staff_id, notification_text)
        except Exception as e:
            print(f"Не удалось отправить уведомление {staff_id}: {e}")
    
    await state.clear()

# --- АДМИН ПАНЕЛЬ (OWNER_ID и DEV_ID) ---
@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if not is_admin(message.from_user.id): 
        return
    
    staff_name = message.from_user.full_name or "Админ"
    role = "ГЛАВНЫЙ АДМИН" if message.from_user.id == OWNER_ID else "РАЗРАБОТЧИК"
    
    await message.answer(
        f"🛠 <b>ПАНЕЛЬ АДМИНИСТРАТОРА</b>\n"
        f"👑 <b>Вы вошли как:</b> {staff_name}\n"
        f"🎖 <b>Роль:</b> {role}\n"
        f"📊 <b>Активных тикетов:</b> {len(pending_tickets)}",
        reply_markup=admin_menu_kb()
    )

@dp.callback_query(F.data == "adm_tickets")
async def adm_tickets(call: types.CallbackQuery):
    if not is_admin(call.from_user.id):
        return await call.answer("⛔️ Доступ запрещен", show_alert=True)
    
    if not pending_tickets: 
        await call.answer("📭 Активных тикетов нет", show_alert=True)
        return
    
    kb = InlineKeyboardBuilder()
    for uid, data in pending_tickets.items():
        btn_text = f"✉️ {data['user'][:15]}"
        if len(data['text']) > 30:
            btn_text += f" | {data['text'][:30]}..."
        else:
            btn_text += f" | {data['text']}"
        kb.row(InlineKeyboardButton(text=btn_text, callback_data=f"view_ticket_{uid}"))
    
    kb.row(InlineKeyboardButton(text="⬅️ НАЗАД", callback_data="adm_back"))
    await call.message.answer(f"📨 <b>АКТИВНЫЕ ТИКЕТЫ ({len(pending_tickets)})</b>", reply_markup=kb.as_markup())

# --- ПАНЕЛЬ МОДЕРАТОРА ---
@dp.message(Command("moder"))
async def cmd_moder(message: types.Message):
    if not is_moderator(message.from_user.id): 
        return
    
    staff_name = message.from_user.full_name or "Модератор"
    role = "АДМИН" if is_admin(message.from_user.id) else "МОДЕРАТОР"
    
    await message.answer(
        f"🛠 <b>ПАНЕЛЬ МОДЕРАТОРА</b>\n"
        f"👤 <b>Вы вошли как:</b> {staff_name}\n"
        f"🎖 <b>Роль:</b> {role}\n"
        f"📊 <b>Активных тикетов:</b> {len(pending_tickets)}",
        reply_markup=moder_menu_kb()
    )

@dp.callback_query(F.data == "mod_tickets")
async def mod_tickets(call: types.CallbackQuery):
    if not is_moderator(call.from_user.id):
        return await call.answer("⛔️ Доступ запрещен", show_alert=True)
    
    if not pending_tickets: 
        await call.answer("📭 Активных тикетов нет", show_alert=True)
        return
    
    kb = InlineKeyboardBuilder()
    for uid, data in pending_tickets.items():
        btn_text = f"✉️ {data['user'][:15]}"
        if len(data['text']) > 30:
            btn_text += f" | {data['text'][:30]}..."
        else:
            btn_text += f" | {data['text']}"
        kb.row(InlineKeyboardButton(text=btn_text, callback_data=f"view_ticket_{uid}"))
    
    kb.row(InlineKeyboardButton(text="⬅️ НАЗАД", callback_data="mod_back"))
    await call.message.answer(f"📨 <b>АКТИВНЫЕ ТИКЕТЫ ({len(pending_tickets)})</b>", reply_markup=kb.as_markup())

@dp.callback_query(F.data == "mod_back")
async def mod_back(call: types.CallbackQuery):
    if not is_moderator(call.from_user.id):
        return await call.answer("⛔️ Доступ запрещен", show_alert=True)
    
    await cmd_moder(call.message)

# --- ОБЩИЕ ХЕНДЛЕРЫ ТИКЕТОВ ---
@dp.callback_query(F.data.startswith("view_ticket_"))
async def view_ticket(call: types.CallbackQuery):
    # Проверяем доступ (админ или модератор)
    if not (is_admin(call.from_user.id) or is_moderator(call.from_user.id)):
        return await call.answer("⛔️ Доступ запрещен", show_alert=True)
    
    uid = int(call.data.split("_")[2])
    ticket = pending_tickets.get(uid)
    if not ticket: 
        return await call.answer("Тикет уже закрыт.", show_alert=True)
    
    text = (
        f"📨 <b>ТИКЕТ ОТ ПОЛЬЗОВАТЕЛЯ</b>\n\n"
        f"👤 <b>Имя:</b> {ticket['user']}\n"
        f"🆔 <b>ID:</b> <code>{uid}</code>\n"
        f"📛 <b>Username:</b> @{ticket['username']}\n\n"
        f"💬 <b>Сообщение:</b>\n<code>{ticket['text']}</code>\n\n"
        f"⏰ <b>Получено:</b> {datetime.now().strftime('%H:%M %d.%m.%Y')}"
    )
    
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="✍️ ОТВЕТИТЬ", callback_data=f"rep_to_{uid}"),
        InlineKeyboardButton(text="⛔️ ЗАБАНИТЬ", callback_data=f"ban_menu_{uid}")
    )
    
    # Определяем, откуда пришли (админ или модер)
    if is_admin(call.from_user.id):
        kb.row(
            InlineKeyboardButton(text="❌ ЗАКРЫТЬ БЕЗ ОТВЕТА", callback_data=f"close_ticket_{uid}"),
            InlineKeyboardButton(text="⬅️ НАЗАД", callback_data="adm_tickets")
        )
    else:
        kb.row(
            InlineKeyboardButton(text="❌ ЗАКРЫТЬ БЕЗ ОТВЕТА", callback_data=f"close_ticket_{uid}"),
            InlineKeyboardButton(text="⬅️ НАЗАД", callback_data="mod_tickets")
        )
    
    await call.message.answer(text, reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("rep_to_"))
async def rep_start(call: types.CallbackQuery, state: FSMContext):
    # Проверяем доступ
    if not (is_admin(call.from_user.id) or is_moderator(call.from_user.id)):
        return await call.answer("⛔️ Доступ запрещен", show_alert=True)
    
    uid = int(call.data.split("_")[2])
    ticket = pending_tickets.get(uid)
    if not ticket:
        return await call.answer("Тикет уже закрыт.", show_alert=True)
    
    staff_name = call.from_user.full_name or "Модератор"
    await state.update_data(
        target_id=uid,
        target_name=ticket['user'],
        staff_name=staff_name
    )
    
    await call.message.answer(
        f"✍️ <b>ОТВЕТ ДЛЯ {ticket['user']}</b>\n\n"
        f"<i>Ваше имя будет указано в ответе как:</i> <b>{staff_name}</b>\n\n"
        f"Напишите ответ:"
    )
    await state.set_state(States.waiting_for_reply)

@dp.message(States.waiting_for_reply)
async def rep_finish(message: types.Message, state: FSMContext):
    data = await state.get_data()
    uid = data['target_id']
    target_name = data['target_name']
    staff_name = data['staff_name']
    
    try:
        reply_text = (
            f"📨 <b>ОТВЕТ ОТ ПОДДЕРЖКИ</b>\n\n"
            f"<b>Отвечает:</b> {staff_name}\n"
            f"<b>Время:</b> {datetime.now().strftime('%H:%M %d.%m.%Y')}\n\n"
            f"💬 <b>Сообщение:</b>\n{message.text}\n\n"
            f"<i>Если у вас остались вопросы, напишите снова.</i>"
        )
        
        await bot.send_message(uid, reply_text)
        await message.answer(f"✅ <b>Ответ отправлен {target_name}!</b>\n\nТикет закрыт.")
        
        # Удаляем тикет из ожидающих
        pending_tickets.pop(uid, None)
        
        # Логируем ответ
        log_text = (
            f"📤 Ответ на тикет от {staff_name}\n"
            f"👤 Пользователь: {target_name} (ID: {uid})\n"
            f"⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"📝 Ответ: {message.text[:100]}...\n"
            f"────────────────────"
        )
        print(log_text)
        
    except Exception as e:
        await message.answer(f"❌ <b>Ошибка при отправке:</b>\n{str(e)}")
    
    await state.clear()

@dp.callback_query(F.data.startswith("close_ticket_"))
async def close_ticket(call: types.CallbackQuery):
    # Проверяем доступ
    if not (is_admin(call.from_user.id) or is_moderator(call.from_user.id)):
        return await call.answer("⛔️ Доступ запрещен", show_alert=True)
    
    uid = int(call.data.split("_")[2])
    ticket = pending_tickets.pop(uid, None)
    
    if ticket:
        try:
            await bot.send_message(uid, "📭 <b>Ваш тикет был закрыт модератором без ответа.</b>\n\nЕсли вопрос остался, создайте новый тикет.")
        except:
            pass
        
        await call.answer(f"Тикет от {ticket['user']} закрыт", show_alert=True)
    
    # Возвращаемся в нужное меню
    if is_admin(call.from_user.id):
        await adm_tickets(call)
    else:
        await mod_tickets(call)

# --- СИСТЕМА БАНОВ (ТОЛЬКО ДЛЯ АДМИНОВ) ---
@dp.callback_query(F.data.startswith("ban_menu_"))
async def ban_menu_handler(call: types.CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return await call.answer("⛔️ Только администратор может банить", show_alert=True)
    
    uid = int(call.data.split("_")[2])
    ticket = pending_tickets.get(uid)
    
    if not ticket:
        return await call.answer("Пользователь не найден", show_alert=True)
    
    # Проверяем, не забанен ли уже пользователь
    if is_user_banned(uid):
        ban_info = get_ban_info(uid)
        if ban_info:
            ban_until = datetime.fromisoformat(ban_info['until'])
            time_left = ban_until - datetime.now()
            hours_left = int(time_left.total_seconds() // 3600)
            minutes_left = int((time_left.total_seconds() % 3600) // 60)
            
            kb = InlineKeyboardBuilder()
            kb.row(InlineKeyboardButton(text="🔓 РАЗБАНИТЬ", callback_data=f"unban_{uid}"))
            kb.row(InlineKeyboardButton(text="⬅️ НАЗАД", callback_data=f"view_ticket_{uid}"))
            
            await call.message.answer(
                f"⛔️ <b>ПОЛЬЗОВАТЕЛЬ УЖЕ ЗАБАНЕН</b>\n\n"
                f"👤 <b>Имя:</b> {ticket['user']}\n"
                f"🆔 <b>ID:</b> <code>{uid}</code>\n\n"
                f"<b>Причина бана:</b> {ban_info.get('reason', 'Не указана')}\n"
                f"<b>Забанил:</b> {ban_info['banned_by']}\n"
                f"<b>Когда:</b> {datetime.fromisoformat(ban_info['banned_at']).strftime('%d.%m.%Y %H:%M')}\n"
                f"<b>Длительность:</b> {ban_info['duration_hours']} часов\n"
                f"<b>Разблокировка:</b> {ban_until.strftime('%d.%m.%Y %H:%M')}\n"
                f"<b>Осталось:</b> {hours_left}ч {minutes_left}м",
                reply_markup=kb.as_markup()
            )
            return
    
    await state.update_data(
        ban_user_id=uid,
        ban_user_name=ticket['user']
    )
    
    await call.message.answer(
        f"⛔️ <b>БАН ПОЛЬЗОВАТЕЛЯ</b>\n\n"
        f"👤 <b>Имя:</b> {ticket['user']}\n"
        f"🆔 <b>ID:</b> <code>{uid}</code>\n\n"
        f"<b>Выберите длительность бана:</b>\n"
        f"<i>Пользователь не сможет писать в поддержку до разблокировки</i>",
        reply_markup=ban_options_kb(uid)
    )

@dp.callback_query(F.data.startswith("ban_"))
async def ban_user_handler(call: types.CallbackQuery):
    if not is_admin(call.from_user.id):
        return await call.answer("⛔️ Только администратор может банить", show_alert=True)
    
    parts = call.data.split("_")
    uid = int(parts[1])
    duration = parts[2]
    
    ticket = pending_tickets.get(uid, {})
    user_name = ticket.get('user', 'Пользователь')
    staff_name = call.from_user.full_name or "Администратор"
    
    if duration == "perm":
        duration_hours = 87600  # 10 лет (фактически навсегда)
        duration_text = "НАВСЕГДА"
    else:
        duration_hours = int(duration)
        if duration_hours < 24:
            duration_text = f"{duration_hours} часов"
        elif duration_hours == 24:
            duration_text = "1 день"
        elif duration_hours < 168:
            duration_text = f"{duration_hours // 24} дня"
        else:
            duration_text = f"{duration_hours // 24} дней"
    
    # Баним пользователя
    ban_until = ban_user(uid, duration_hours, staff_name, "Нарушение правил поддержки")
    
    # Уведомляем пользователя
    try:
        await bot.send_message(
            uid,
            f"⛔️ <b>ВЫ ЗАБАНЕНЫ В ПОДДЕРЖКЕ</b>\n\n"
            f"<b>Причина:</b> Нарушение правил использования поддержки\n"
            f"<b>Забанил:</b> {staff_name}\n"
            f"<b>Длительность:</b> {duration_text}\n"
            f"<b>Разблокировка:</b> {ban_until.strftime('%d.%m.%Y в %H:%M')}\n\n"
            f"<i>Вы не можете писать в поддержку до разблокировки.</i>"
        )
    except:
        pass
    
    # Удаляем тикет пользователя
    pending_tickets.pop(uid, None)
    
    # Отправляем уведомление админу
    await call.answer(f"✅ {user_name} забанен на {duration_text}", show_alert=True)
    
    # Возвращаемся к списку тикетов
    if is_admin(call.from_user.id):
        await adm_tickets(call)
    else:
        await mod_tickets(call)

@dp.callback_query(F.data.startswith("unban_"))
async def unban_user_handler(call: types.CallbackQuery):
    if not is_admin(call.from_user.id):
        return await call.answer("⛔️ Только администратор может разбанивать", show_alert=True)
    
    uid = int(call.data.split("_")[1])
    
    if unban_user(uid):
        try:
            await bot.send_message(
                uid,
                "✅ <b>ВАШ БАН СНЯТ</b>\n\n"
                "Вы снова можете писать в поддержку.\n"
                "Пожалуйста, соблюдайте правила общения."
            )
        except:
            pass
        
        await call.answer("✅ Пользователь разбанен", show_alert=True)
    else:
        await call.answer("❌ Пользователь не был забанен", show_alert=True)
    
    # Возвращаемся к списку тикетов
    if is_admin(call.from_user.id):
        await adm_tickets(call)
    else:
        await mod_tickets(call)

@dp.callback_query(F.data.startswith("cancel_ban_"))
async def cancel_ban_handler(call: types.CallbackQuery):
    uid = int(call.data.split("_")[2])
    await view_ticket(call)

@dp.callback_query(F.data == "adm_bans")
async def show_ban_management(call: types.CallbackQuery):
    if not is_admin(call.from_user.id):
        return await call.answer("⛔️ Только администратор имеет доступ к системе банов", show_alert=True)
    
    banned_users = load_banned_users()
    active_bans = 0
    
    # Удаляем просроченные баны
    for user_str in list(banned_users.keys()):
        ban_info = banned_users[user_str]
        ban_until = datetime.fromisoformat(ban_info['until'])
        if datetime.now() > ban_until:
            del banned_users[user_str]
        else:
            active_bans += 1
    
    save_banned_users(banned_users)
    
    if active_bans == 0:
        text = "⛔️ <b>СИСТЕМА БАНОВ</b>\n\nНет активных банов."
    else:
        text = f"⛔️ <b>СИСТЕМА БАНОВ</b>\n\nАктивных банов: {active_bans}"
    
    await call.message.answer(text, reply_markup=ban_management_kb())

@dp.callback_query(F.data == "list_banned")
async def list_banned_users(call: types.CallbackQuery):
    if not is_admin(call.from_user.id):
        return await call.answer("⛔️ Только администратор имеет доступ к системе банов", show_alert=True)
    
    banned_users = load_banned_users()
    
    if not banned_users:
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text="⬅️ НАЗАД", callback_data="adm_bans"))
        return await call.message.answer("📋 <b>СПИСОК ЗАБАНЕННЫХ ПУСТ</b>", reply_markup=kb.as_markup())
    
    text = "📋 <b>АКТИВНЫЕ БАНЫ:</b>\n\n"
    
    for i, (user_str, ban_info) in enumerate(banned_users.items(), 1):
        ban_until = datetime.fromisoformat(ban_info['until'])
        
        if datetime.now() > ban_until:
            continue
        
        time_left = ban_until - datetime.now()
        hours_left = int(time_left.total_seconds() // 3600)
        minutes_left = int((time_left.total_seconds() % 3600) // 60)
        
        text += (
            f"{i}. 👤 <b>ID:</b> <code>{user_str}</code>\n"
            f"   ⏰ <b>До:</b> {ban_until.strftime('%d.%m.%Y %H:%M')}\n"
            f"   ⏳ <b>Осталось:</b> {hours_left}ч {minutes_left}м\n"
            f"   👮 <b>Забанил:</b> {ban_info['banned_by']}\n"
            f"   📝 <b>Причина:</b> {ban_info.get('reason', 'Не указана')}\n\n"
        )
    
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="🔙 В МЕНЮ БАНОВ", callback_data="adm_bans"))
    kb.row(InlineKeyboardButton(text="⬅️ В АДМИНКУ", callback_data="adm_back"))
    
    await call.message.answer(text, reply_markup=kb.as_markup())

@dp.callback_query(F.data == "adm_broadcast")
async def broad_init(call: types.CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return await call.answer("⛔️ Только администратор может делать рассылку", show_alert=True)
    
    await call.message.answer("📢 <b>Введите текст рассылки:</b>")
    await state.set_state(States.waiting_for_broadcast)

@dp.message(States.waiting_for_broadcast)
async def broad_send(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    if not os.path.exists(DB_USERS): 
        await message.answer("❌ База пользователей пуста")
        await state.clear()
        return
    
    with open(DB_USERS, "r") as f: 
        users = f.read().splitlines()
    
    if not users:
        await message.answer("❌ Нет пользователей для рассылки")
        await state.clear()
        return
    
    await message.answer(f"🚀 <b>Начинаю рассылку на {len(users)} пользователей...</b>")
    
    count = 0
    failed = 0
    
    for u in users:
        try:
            await bot.send_message(u, f"📢 <b>ОБЪЯВЛЕНИЕ ОТ АКАДЕМИИ:</b>\n\n{message.text}")
            count += 1
            await asyncio.sleep(0.05)
        except Exception as e:
            failed += 1
    
    await message.answer(
        f"✅ <b>РАССЫЛКА ЗАВЕРШЕНА</b>\n\n"
        f"📊 <b>Статистика:</b>\n"
        f"• Отправлено: {count}\n"
        f"• Не доставлено: {failed}\n"
        f"• Всего в базе: {len(users)}"
    )
    await state.clear()

@dp.callback_query(F.data == "adm_back")
async def adm_back(call: types.CallbackQuery):
    if not is_admin(call.from_user.id):
        return await call.answer("⛔️ Доступ запрещен", show_alert=True)
    
    await call.message.answer("🛠 <b>ПАНЕЛЬ АДМИНИСТРАТОРА</b>", reply_markup=admin_menu_kb())

# --- МЕНЮ МОДЕРАТОРОВ (ТОЛЬКО ДЛЯ АДМИНОВ) ---
@dp.callback_query(F.data == "adm_mods")
async def show_mods_menu(call: types.CallbackQuery):
    if not is_admin(call.from_user.id):
        return await call.answer("⛔️ Только администратор может управлять модераторами", show_alert=True)
    
    text = "👤 <b>УПРАВЛЕНИЕ МОДЕРАТОРАМИ</b>\n\n"
    
    # Показываем список текущих модераторов
    if os.path.exists(MODS_FILE):
        with open(MODS_FILE, "r") as f:
            mods = f.read().splitlines()
        
        if mods:
            text += f"<b>Текущие модераторы ({len(mods)}):</b>\n"
            for i, mod_id in enumerate(mods, 1):
                if mod_id.strip():
                    text += f"{i}. <code>{mod_id}</code>\n"
        else:
            text += "📭 <i>Модераторов пока нет</i>\n"
    else:
        text += "📭 <i>Модераторов пока нет</i>\n"
    
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="➕ ДОБАВИТЬ МОДЕРА", callback_data="add_mod"),
        InlineKeyboardButton(text="➖ УДАЛИТЬ МОДЕРА", callback_data="remove_mod")
    )
    kb.row(InlineKeyboardButton(text="⬅️ НАЗАД", callback_data="adm_back"))
    
    await call.message.answer(text, reply_markup=kb.as_markup())

@dp.callback_query(F.data == "add_mod")
async def start_add_mod(call: types.CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return await call.answer("⛔️ Только администратор может добавлять модераторов", show_alert=True)
    
    await call.message.answer(
        "👤 <b>ДОБАВЛЕНИЕ МОДЕРАТОРА</b>\n\n"
        "Пришлите ID пользователя, которого хотите сделать модератором.\n"
        "<i>ID можно получить с помощью бота @userinfobot</i>"
    )
    await state.set_state(States.adding_mod)

@dp.message(States.adding_mod)
async def add_mod_finish(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    try:
        mod_id = int(message.text.strip())
        
        # Проверяем, не админ ли уже
        if mod_id in [OWNER_ID, DEV_ID]:
            await message.answer("❌ <b>Этот пользователь уже является админом!</b>")
            await state.clear()
            return
        
        # Проверяем, не модер ли уже
        if os.path.exists(MODS_FILE):
            with open(MODS_FILE, "r") as f:
                mods = f.read().splitlines()
            
            if str(mod_id) in mods:
                await message.answer("❌ <b>Этот пользователь уже модератор!</b>")
                await state.clear()
                return
        
        # Добавляем модератора
        with open(MODS_FILE, "a") as f:
            f.write(f"{mod_id}\n")
        
        await message.answer(f"✅ <b>Пользователь {mod_id} добавлен в модераторы!</b>")
        
        # Уведомляем нового модера
        try:
            await bot.send_message(
                mod_id,
                "🎉 <b>ВЫ НАЗНАЧЕНЫ МОДЕРАТОРОМ В ACADEMY SPLIT!</b>\n\n"
                f"Вас назначил: {message.from_user.full_name or 'Администратор'}\n\n"
                "Доступные команды:\n"
                "• <code>/moder</code> - панель модератора\n"
                "• Просмотр тикетов поддержки\n"
                "• Ответы на вопросы пользователей\n\n"
                "<i>Используйте свои полномочия с умом!</i>"
            )
        except:
            pass
        
    except ValueError:
        await message.answer("❌ <b>Неверный ID!</b>\nID должен состоять только из цифр.")
    except Exception as e:
        await message.answer(f"❌ <b>Ошибка:</b> {str(e)}")
    
    await state.clear()

@dp.callback_query(F.data == "remove_mod")
async def start_remove_mod(call: types.CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return await call.answer("⛔️ Только администратор может удалять модераторов", show_alert=True)
    
    if not os.path.exists(MODS_FILE):
        return await call.answer("❌ Список модераторов пуст", show_alert=True)
    
    with open(MODS_FILE, "r") as f:
        mods = f.read().splitlines()
    
    if not mods:
        return await call.answer("❌ Список модераторов пуст", show_alert=True)
    
    # Создаем клавиатуру с кнопками для удаления
    kb = InlineKeyboardBuilder()
    for mod_id in mods:
        if mod_id.strip():
            kb.row(InlineKeyboardButton(text=f"❌ Удалить модератора {mod_id}", callback_data=f"rm_mod_{mod_id}"))
    
    kb.row(InlineKeyboardButton(text="⬅️ НАЗАД", callback_data="adm_mods"))
    
    await call.message.answer(
        "➖ <b>УДАЛЕНИЕ МОДЕРАТОРА</b>\n\n"
        "Выберите модератора для удаления:",
        reply_markup=kb.as_markup()
    )

@dp.callback_query(F.data.startswith("rm_mod_"))
async def remove_mod_finish(call: types.CallbackQuery):
    if not is_admin(call.from_user.id):
        return await call.answer("⛔️ Только администратор может удалять модераторов", show_alert=True)
    
    mod_id = call.data.split("_")[2]
    
    try:
        # Читаем всех модеров кроме удаляемого
        with open(MODS_FILE, "r") as f:
            mods = f.read().splitlines()
        
        new_mods = [m for m in mods if m != mod_id]
        
        # Записываем обновленный список
        with open(MODS_FILE, "w") as f:
            f.write("\n".join(new_mods))
        
        await call.answer(f"✅ Модератор {mod_id} удален!", show_alert=True)
        
        # Уведомляем удаленного модера
        try:
            await bot.send_message(
                int(mod_id),
                "⚠️ <b>ВАШИ ПОЛНОМОЧИЯ МОДЕРАТОРА ОТОЗВАНЫ</b>\n\n"
                f"Вас удалил: {call.from_user.full_name or 'Администратор'}\n\n"
                "<i>Доступ к панели модератора закрыт.</i>"
            )
        except:
            pass
        
        # Возвращаемся в меню модераторов
        await show_mods_menu(call)
        
    except Exception as e:
        await call.answer(f"❌ Ошибка: {str(e)}", show_alert=True)

# --- ЗАПУСК ---
async def main():
    # Визуал запуска
    startup_visual()
    
    # Проверяем и чистим просроченные баны при запуске
    banned_users = load_banned_users()
    cleaned = 0
    for user_str in list(banned_users.keys()):
        ban_info = banned_users[user_str]
        ban_until = datetime.fromisoformat(ban_info['until'])
        if datetime.now() > ban_until:
            del banned_users[user_str]
            cleaned += 1
    
    if cleaned > 0:
        save_banned_users(banned_users)
        console.print(f"[bold yellow]Очищено просроченных банов: {cleaned}[/bold yellow]")
    
    # Удаляем вебхуки и запускаем поллинг
    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dp.start_polling(bot)
    except Exception as e:
        console.print(f"[bold red]Ошибка при запуске бота: {e}[/bold red]")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass