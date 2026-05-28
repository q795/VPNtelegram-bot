"""
VPN Telegram Bot - Главный файл бота
"""
import logging
import io
import qrcode
from datetime import datetime
from typing import Optional

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.filters import Command, CommandStart
from aiogram.enums import ParseMode
from aiogram.utils.chat_action import ChatActionSender

from config import BOT_TOKEN, TARIFFS, DEMO_SERVERS, DEMO_TRAFFIC_MB, DEMO_DURATION_DAYS
from database import db
from vless_generator import vless_gen
import keyboards as kb
import texts

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаём роутер
router = Router()


# === Команды ===

@router.message(CommandStart())
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    user = db.create_user(
        user_id=message.from_user.id,
        username=message.from_user.username or "",
        first_name=message.from_user.first_name or ""
    )

    await message.answer(
        texts.WELCOME,
        parse_mode=ParseMode.HTML,
        reply_markup=kb.get_main_menu()
    )


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    """Обработчик команды /menu"""
    await message.answer(
        "📱 <b>Главное меню</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=kb.get_main_menu()
    )


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Обработчик команды /stats (для админа)"""
    stats = db.get_stats()
    await message.answer(
        texts.STATS_INFO.format(
            total_users=stats.get("total_users", 0),
            total_trials=stats.get("total_trials", 0),
            total_subscriptions=stats.get("total_subscriptions", 0)
        ),
        parse_mode=ParseMode.HTML
    )


# === Callbacks ===

@router.callback_query(F.data == "back_to_menu")
async def callback_back_to_menu(callback: CallbackQuery):
    """Возврат в главное меню"""
    await callback.message.edit_text(
        "📱 <b>Главное меню</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=kb.get_main_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "profile")
async def callback_profile(callback: CallbackQuery):
    """Просмотр профиля"""
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    subscription = db.get_subscription(user_id)
    traffic_info = db.get_traffic_info(user_id)

    # Формируем информацию о пользователе
    user_info = f"👤 <b>{user.get('first_name', 'Пользователь')}</b>"
    if user.get('username'):
        user_info += f" (@{user.get('username')})"

    if subscription:
        expires = datetime.fromisoformat(subscription['expires_at'])
        expires_str = expires.strftime("%d.%m.%Y %H:%M")

        if subscription['is_trial']:
            status_text = texts.STATUS_TRIAL.format(
                expires=expires_str,
                remaining=traffic_info.get('remaining_mb', 0)
            )
        else:
            status_text = texts.STATUS_ACTIVE.format(expires=expires_str)

        # Прогресс-бар
        used_percent = traffic_info.get('used_percent', 0)
        filled = int(used_percent // 10)
        bar = "▓" * filled + "░" * (10 - filled)

        traffic_text = texts.TRAFFIC_INFO.format(
            used_mb=traffic_info.get('used_mb', 0),
            total_mb=traffic_info.get('total_mb', 0),
            filled_bar=bar,
            used_percent=used_percent,
            remaining_mb=traffic_info.get('remaining_mb', 0)
        )

        profile_text = texts.PROFILE.format(
            user_info=user_info,
            status_text=status_text,
            traffic_text=traffic_text
        )

        reply_markup = kb.get_profile_keyboard(
            has_subscription=True,
            is_trial=subscription['is_trial']
        )
    else:
        profile_text = texts.PROFILE_NO_SUB
        reply_markup = kb.get_profile_keyboard(has_subscription=False)

    await callback.message.edit_text(
        profile_text,
        parse_mode=ParseMode.HTML,
        reply_markup=reply_markup
    )
    await callback.answer()


@router.callback_query(F.data == "get_vpn")
async def callback_get_vpn(callback: CallbackQuery):
    """Получить VPN"""
    user_id = callback.from_user.id
    subscription = db.get_subscription(user_id)

    if not subscription:
        await callback.message.edit_text(
            texts.NO_SUBSCRIPTION,
            parse_mode=ParseMode.HTML,
            reply_markup=kb.get_profile_keyboard(has_subscription=False)
        )
        await callback.answer()
        return

    # Показываем информацию о серверах
    server_list = "\n".join([
        f"• {srv['name']}" for srv in DEMO_SERVERS
    ])

    await callback.message.edit_text(
        f"🔗 <b>Ваши VLESS-конфиги</b>\n\n"
        f"<b>🖥 Сервер:</b> {DEMO_SERVERS[0]['name']}\n\n"
        f"<b>🔑 UUID:</b> <code>{vless_gen.generate_uuid()}</code>\n\n"
        f"<b>📡 Серверы:</b>\n{server_list}\n\n"
        f"Нажмите «📱 QR-код» или «📥 Скачать конфиг» в профиле.",
        parse_mode=ParseMode.HTML,
        reply_markup=kb.get_profile_keyboard(
            has_subscription=True,
            is_trial=subscription['is_trial']
        )
    )
    await callback.answer()


@router.callback_query(F.data == "qr_code")
async def callback_qr_code(callback: CallbackQuery):
    """Генерация QR-кода"""
    user_id = callback.from_user.id
    subscription = db.get_subscription(user_id)

    if not subscription:
        await callback.answer("❌ Нет подписки", show_alert=True)
        return

    await callback.message.edit_text(
        texts.QR_INSTRUCTIONS,
        parse_mode=ParseMode.HTML
    )

    # Генерируем демо-VLESS ссылку
    config = vless_gen.create_demo_config(user_id)
    vless_link = config['configs'][0]['link']

    # Создаём QR-код
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(vless_link)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Сохраняем в буфер
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    await callback.message.answer_photo(
        photo=BufferedInputFile(buffer.getvalue(), filename="vpn_qr.png"),
        caption=f"📱 <b>QR-код для {config['default_server']}</b>\n\n"
                f"Отсканируйте в приложении V2rayNG",
        parse_mode=ParseMode.HTML,
        reply_markup=kb.get_back_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "download_config")
async def callback_download_config(callback: CallbackQuery):
    """Скачивание конфига"""
    user_id = callback.from_user.id
    subscription = db.get_subscription(user_id)

    if not subscription:
        await callback.answer("❌ Нет подписки", show_alert=True)
        return

    # Генерируем конфиг
    config = vless_gen.create_demo_config(user_id)

    # Формируем текстовый конфиг
    config_text = f"# VLESS VPN Конфиг\n"
    config_text += f"# User ID: {user_id}\n"
    config_text += f"# Created: {datetime.now().isoformat()}\n\n"

    for cfg in config['configs']:
        config_text += f"## {cfg['server']}\n"
        config_text += f"{cfg['link']}\n\n"

    # Отправляем файл
    file_buffer = io.BytesIO(config_text.encode())
    file_buffer.name = "vpn_config.txt"

    await callback.message.answer_document(
        document=BufferedInputFile(file_buffer.getvalue(), filename="vpn_config.txt"),
        caption=f"📥 <b>Конфиг для {config['default_server']}</b>\n\n"
                f"Импортируйте в V2rayNG или другое VPN-приложение",
        parse_mode=ParseMode.HTML,
        reply_markup=kb.get_back_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "tariffs")
async def callback_tariffs(callback: CallbackQuery):
    """Просмотр тарифов"""
    tariff_list = "\n".join([
        f"• {t['name']} - {t['price']}₽ ({t['traffic_gb']} ГБ)"
        for t in TARIFFS
    ])

    await callback.message.edit_text(
        texts.TARIFFS_INFO.format(
            trial_mb=DEMO_TRAFFIC_MB,
            trial_days=DEMO_DURATION_DAYS
        ),
        parse_mode=ParseMode.HTML,
        reply_markup=kb.get_tariffs_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "trial")
async def callback_trial(callback: CallbackQuery):
    """Информация о пробном периоде"""
    user_id = callback.from_user.id
    user = db.get_user(user_id)

    if user and user.get('trials_used', 0) >= 1:
        await callback.message.edit_text(
            texts.TRIAL_LIMIT,
            parse_mode=ParseMode.HTML,
            reply_markup=kb.get_tariffs_keyboard()
        )
    else:
        await callback.message.edit_text(
            texts.TRIAL_INFO.format(
                traffic_mb=DEMO_TRAFFIC_MB,
                days=DEMO_DURATION_DAYS,
                server_count=len(DEMO_SERVERS)
            ),
            parse_mode=ParseMode.HTML,
            reply_markup=kb.get_confirm_trial_keyboard()
        )

    await callback.answer()


@router.callback_query(F.data == "confirm_trial")
async def callback_confirm_trial(callback: CallbackQuery):
    """Подтверждение пробного периода"""
    user_id = callback.from_user.id

    # Проверяем и увеличиваем счётчик
    can_trial = db.increment_trial(user_id)

    if not can_trial:
        await callback.message.edit_text(
            texts.TRIAL_LIMIT,
            parse_mode=ParseMode.HTML,
            reply_markup=kb.get_tariffs_keyboard()
        )
        await callback.answer("❌ Пробный период недоступен", show_alert=True)
        return

    # Создаём подписку
    subscription = db.create_subscription(
        user_id=user_id,
        tariff_id="trial",
        is_trial=True
    )

    await callback.message.edit_text(
        texts.TRIAL_SUCCESS.format(
            traffic_mb=DEMO_TRAFFIC_MB,
            days=DEMO_DURATION_DAYS,
            server=DEMO_SERVERS[0]['name']
        ),
        parse_mode=ParseMode.HTML,
        reply_markup=kb.get_profile_keyboard(has_subscription=True, is_trial=True)
    )
    await callback.answer("🎉 Пробный период активирован!")


# Обработка покупки тарифов
@router.callback_query(F.data.startswith("buy_"))
async def callback_buy(callback: CallbackQuery):
    """Обработка покупки"""
    tariff_id = callback.data.replace("buy_", "")

    # Находим тариф
    tariff = next((t for t in TARIFFS if t['id'] == tariff_id), None)
    if not tariff:
        await callback.answer("❌ Тариф не найден")
        return

    # Создаём демо-платёж
    payment = db.create_payment(
        user_id=callback.from_user.id,
        tariff_id=tariff_id,
        amount=tariff['price']
    )

    await callback.message.edit_text(
        texts.PAYMENT_DEMO.format(
            tariff_name=tariff['name'],
            price=tariff['price']
        ),
        parse_mode=ParseMode.HTML,
        reply_markup=kb.get_demo_payment_keyboard(payment['id'])
    )
    await callback.answer()


# Обработка демо-оплаты
@router.callback_query(F.data.startswith("demo_pay_"))
async def callback_demo_payment(callback: CallbackQuery):
    """Демо-подтверждение оплаты"""
    payment_id = callback.data.replace("demo_pay_", "")

    # Подтверждаем платёж
    payment = db.complete_payment(payment_id)

    if not payment:
        await callback.answer("❌ Платёж не найден", show_alert=True)
        return

    # Находим тариф
    tariff = next((t for t in TARIFFS if t['id'] == payment['tariff_id']), None)
    if tariff:
        # Создаём подписку
        subscription = db.create_subscription(
            user_id=callback.from_user.id,
            tariff_id=tariff['id'],
            is_trial=False
        )

        await callback.message.edit_text(
            texts.PAYMENT_SUCCESS.format(
                traffic_gb=tariff['traffic_gb'],
                days=tariff['days'],
                server=DEMO_SERVERS[0]['name']
            ),
            parse_mode=ParseMode.HTML,
            reply_markup=kb.get_profile_keyboard(has_subscription=True)
        )
    else:
        await callback.message.edit_text(
            "✅ Платёж подтверждён!",
            reply_markup=kb.get_back_keyboard()
        )

    await callback.answer("✅ Оплата прошла успешно!")


@router.callback_query(F.data == "servers")
async def callback_servers(callback: CallbackQuery):
    """Просмотр серверов"""
    subscription = db.get_subscription(callback.from_user.id)

    server_list = "\n".join([
        f"• {srv['name']}" for srv in DEMO_SERVERS
    ])

    await callback.message.edit_text(
        texts.SERVERS_INFO.format(server_list=server_list),
        parse_mode=ParseMode.HTML,
        reply_markup=kb.get_servers_keyboard(
            selected_server=subscription.get('server_id') if subscription else None
        )
    )
    await callback.answer()


@router.callback_query(F.data.startswith("server_"))
async def callback_select_server(callback: CallbackQuery):
    """Выбор сервера"""
    server_id = int(callback.data.replace("server_", ""))
    server = next((s for s in DEMO_SERVERS if s['id'] == server_id), None)

    if server:
        await callback.answer(f"✅ Выбран сервер: {server['name']}")
    else:
        await callback.answer("❌ Сервер не найден")

    await callback.message.edit_reply_markup(
        reply_markup=kb.get_servers_keyboard(selected_server=server_id)
    )


@router.callback_query(F.data == "stats")
async def callback_stats(callback: CallbackQuery):
    """Статистика"""
    stats = db.get_stats()

    await callback.message.edit_text(
        texts.STATS_INFO.format(
            total_users=stats.get('total_users', 0),
            total_trials=stats.get('total_trials', 0),
            total_subscriptions=stats.get('total_subscriptions', 0)
        ),
        parse_mode=ParseMode.HTML,
        reply_markup=kb.get_back_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "help")
async def callback_help(callback: CallbackQuery):
    """Помощь"""
    await callback.message.edit_text(
        texts.HELP_INFO,
        parse_mode=ParseMode.HTML,
        reply_markup=kb.get_back_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "change_server")
async def callback_change_server(callback: CallbackQuery):
    """Смена сервера"""
    subscription = db.get_subscription(callback.from_user.id)

    if not subscription:
        await callback.answer("❌ Нет активной подписки", show_alert=True)
        return

    await callback.message.edit_text(
        "🔄 <b>Выберите новый сервер</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=kb.get_servers_keyboard(
            selected_server=subscription.get('server_id')
        )
    )
    await callback.answer()


@router.callback_query(F.data == "renew")
async def callback_renew(callback: CallbackQuery):
    """Продление подписки"""
    await callback.message.edit_text(
        "💎 <b>Продление подписки</b>\n\n"
        "Выберите новый тариф для продления:",
        parse_mode=ParseMode.HTML,
        reply_markup=kb.get_tariffs_keyboard()
    )
    await callback.answer()
