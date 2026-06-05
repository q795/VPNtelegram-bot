"""
VPN Telegram Bot - VERA VPN
Улучшенная версия с динамическим меню
"""
import logging
import io
import os
import asyncio
from datetime import datetime, timedelta
from typing import Optional

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile, InputFile
from aiogram.filters import Command, CommandStart
from aiogram.enums import ParseMode
from aiogram.utils.chat_action import ChatActionSender

from config import BOT_TOKEN, TARIFFS, DEMO_SERVERS, ADMIN_IDS, DEMO_DURATION_DAYS
from database import db
import keyboards as kb
import texts

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Пути
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(BASE_DIR, "logo.jpg")
SCREENS_DIR = os.path.join(BASE_DIR, "screens")

SCREEN_PATHS = {
    "profile": os.path.join(SCREENS_DIR, "profile.png"),
    "tariffs": os.path.join(SCREENS_DIR, "tariffs.png"),
    "keys": os.path.join(SCREENS_DIR, "keys.png"),
    "support": os.path.join(SCREENS_DIR, "support.png"),
}

router = Router()


# === Вспомогательные функции ===

async def send_screen(callback: CallbackQuery, screen_key: str, text: str, reply_markup=None):
    """Отправляет фото-скриншот с caption"""
    screen_path = SCREEN_PATHS.get(screen_key)
    if screen_path and os.path.exists(screen_path):
        await callback.message.answer_photo(
            photo=InputFile(screen_path),
            caption=text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    else:
        await callback.message.answer(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )


def get_user_menu_state(user_id: int) -> dict:
    """Получить состояние меню для пользователя"""
    user = db.get_user(user_id)
    subscription = db.get_subscription(user_id)

    trial_used = user.get('trials_used', 0) >= 1 if user else False

    # Пробная кнопка видна только если:
    # 1. trials_used >= 1 (пробный период активирован)
    # ИЛИ
    # 2. Подписка истекла
    show_trial_button = False
    if trial_used and subscription:
        # Пробный активирован, проверяем истёк ли
        show_trial_button = False  # Скрываем после активации
    elif trial_used and not subscription:
        # Пробный был, но истёк - показываем кнопку

    return {
        'has_trial_used': trial_used,
        'has_active_subscription': subscription is not None,
        'is_admin': user_id in ADMIN_IDS
    }


# === Команды ===

@router.message(CommandStart())
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    user_id = message.from_user.id

    db.create_user(
        user_id=user_id,
        username=message.from_user.username or "",
        first_name=message.from_user.first_name or ""
    )

    menu_state = get_user_menu_state(user_id)

    if os.path.exists(LOGO_PATH):
        await message.answer_photo(
            photo=InputFile(LOGO_PATH),
            caption=texts.WELCOME,
            parse_mode=ParseMode.HTML,
            reply_markup=kb.get_main_menu(**menu_state)
        )
    else:
        await message.answer(
            texts.WELCOME,
            parse_mode=ParseMode.HTML,
            reply_markup=kb.get_main_menu(**menu_state)
        )


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    """Обработчик команды /menu"""
    menu_state = get_user_menu_state(message.from_user.id)
    await message.answer(
        texts.MENU_TEXT,
        parse_mode=ParseMode.HTML,
        reply_markup=kb.get_main_menu(**menu_state)
    )


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Панель администратора"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Доступ запрещён")
        return

    await message.answer(
        texts.ADMIN_PANEL,
        parse_mode=ParseMode.HTML,
        reply_markup=kb.get_admin_menu()
    )


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Статистика бота"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Доступ запрещён")
        return

    stats = db.get_full_stats()
    await message.answer(
        texts.ADMIN_STATS.format(
            total_users=stats['total_users'],
            total_trials=stats['total_trials'],
            total_subscriptions=stats['total_subscriptions'],
            active_subs=stats['active_subscriptions'],
            daily_new=stats['daily_new'],
            weekly_new=stats['weekly_new'],
            monthly_new=stats['monthly_new']
        ),
        parse_mode=ParseMode.HTML
    )


# === Callbacks ===

@router.callback_query(F.data == "back_to_menu")
async def callback_back_to_menu(callback: CallbackQuery):
    """Возврат в главное меню"""
    user_id = callback.from_user.id
    menu_state = get_user_menu_state(user_id)

    await callback.message.delete()

    if os.path.exists(LOGO_PATH):
        await callback.message.answer_photo(
            photo=InputFile(LOGO_PATH),
            caption=texts.WELCOME,
            parse_mode=ParseMode.HTML,
            reply_markup=kb.get_main_menu(**menu_state)
        )
    else:
        await callback.message.answer(
            texts.WELCOME,
            parse_mode=ParseMode.HTML,
            reply_markup=kb.get_main_menu(**menu_state)
        )
    await callback.answer()


@router.callback_query(F.data == "profile")
async def callback_profile(callback: CallbackQuery):
    """Просмотр профиля"""
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    subscription = db.get_subscription(user_id)
    trial_used = user.get('trials_used', 0) >= 1 if user else False

    if subscription:
        expires = datetime.fromisoformat(subscription['expires_at'])
        expires_str = expires.strftime("%d.%m.%Y")

        if subscription['is_trial']:
            status_text = texts.STATUS_TRIAL.format(expires=expires_str)
        else:
            status_text = texts.STATUS_ACTIVE.format(expires=expires_str)

        profile_text = texts.PROFILE_ACTIVE.format(
            user_name=user.get('first_name', 'Пользователь'),
            status_text=status_text
        )
        reply_markup = kb.get_profile_keyboard(has_subscription=True)
    elif trial_used:
        profile_text = texts.PROFILE_EXPIRED.format(
            user_name=user.get('first_name', 'Пользователь')
        )
        reply_markup = kb.get_profile_keyboard(
            has_subscription=False,
            trial_expired=True
        )
    else:
        profile_text = texts.PROFILE_NO_SUB.format(
            user_name=user.get('first_name', 'Пользователь')
        )
        reply_markup = kb.get_profile_keyboard(has_subscription=False)

    await callback.message.delete()
    await send_screen(callback, "profile", profile_text, reply_markup)
    await callback.answer()


@router.callback_query(F.data == "my_keys")
async def callback_my_keys(callback: CallbackQuery):
    """Мои ключи"""
    user_id = callback.from_user.id
    subscription = db.get_subscription(user_id)

    if not subscription:
        await callback.message.delete()
        await send_screen(
            callback, "keys",
            texts.KEYS_NO_ACTIVE,
            kb.get_profile_keyboard(has_subscription=False)
        )
        await callback.answer()
        return

    # Генерируем демо-конфиг
    from vless_generator import vless_gen
    config = vless_gen.create_demo_config(user_id)
    main_config = config['configs'][0] if config['configs'] else None

    if main_config:
        vless_link = main_config['link']
        expires = datetime.fromisoformat(subscription['expires_at']).strftime("%d.%m.%Y")

        keys_text = texts.KEYS_ACTIVE.format(
            vless_link=vless_link,
            expires=expires
        )
        reply_markup = kb.get_keys_keyboard(has_subscription=True)
    else:
        keys_text = texts.KEYS_ERROR
        reply_markup = kb.get_back_keyboard()

    await callback.message.delete()
    await send_screen(callback, "keys", keys_text, reply_markup)
    await callback.answer()


@router.callback_query(F.data == "tariffs")
async def callback_tariffs(callback: CallbackQuery):
    """Просмотр тарифов"""
    tariffs_text = texts.TARIFFS_INFO
    await callback.message.delete()
    await send_screen(
        callback, "tariffs",
        tariffs_text,
        kb.get_tariffs_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "trial")
async def callback_trial(callback: CallbackQuery):
    """Активация пробного периода - АВТОМАТИЧЕСКИ"""
    user_id = callback.from_user.id
    user = db.get_user(user_id)

    if not user:
        await callback.answer("❌ Ошибка пользователя", show_alert=True)
        return

    # Проверяем, не использовал ли уже пробный период
    if user.get('trials_used', 0) >= 1:
        await callback.message.delete()
        await send_screen(
            callback, "welcome",
            texts.TRIAL_LIMIT,
            kb.get_tariffs_keyboard()
        )
        await callback.answer()
        return

    # АВТОАКТИВАЦИЯ пробного периода
    db.increment_trial(user_id)
    subscription = db.create_subscription(
        user_id=user_id,
        tariff_id="trial",
        is_trial=True
    )

    expires = datetime.fromisoformat(subscription['expires_at']).strftime("%d.%m.%Y")

    # Показываем экран успеха с кнопкой "Мои ключи"
    await callback.message.delete()
    await send_screen(
        callback, "welcome",
        texts.TRIAL_SUCCESS.format(expires=expires),
        kb.get_trial_success_keyboard()
    )
    await callback.answer("🎉 Пробный период активирован!")


@router.callback_query(F.data == "confirm_trial")
async def callback_confirm_trial(callback: CallbackQuery):
    """Подтверждение пробного периода (дублирующий)"""
    # Просто редиректим на trial
    await callback_trial(callback)


# Обработка покупки тарифов
@router.callback_query(F.data.startswith("buy_"))
async def callback_buy(callback: CallbackQuery):
    """Обработка покупки"""
    tariff_id = callback.data.replace("buy_", "")
    tariff = next((t for t in TARIFFS if t['id'] == tariff_id), None)

    if not tariff:
        await callback.answer("❌ Тариф не найден")
        return

    # Демо-платёж
    payment = db.create_payment(
        user_id=callback.from_user.id,
        tariff_id=tariff_id,
        amount=tariff['price']
    )

    payment_text = texts.PAYMENT_DEMO.format(
        tariff_name=tariff['name'],
        price=tariff['price'],
        monthly_price=tariff.get('monthly_price', tariff['price'])
    )

    await callback.message.edit_text(
        payment_text,
        parse_mode=ParseMode.HTML,
        reply_markup=kb.get_demo_payment_keyboard(payment['id'])
    )
    await callback.answer()


# Демо-подтверждение оплаты
@router.callback_query(F.data.startswith("demo_pay_"))
async def callback_demo_payment(callback: CallbackQuery):
    """Демо-подтверждение оплаты"""
    payment_id = callback.data.replace("demo_pay_", "")
    payment = db.complete_payment(payment_id)

    if not payment:
        await callback.answer("❌ Платёж не найден", show_alert=True)
        return

    tariff = next((t for t in TARIFFS if t['id'] == payment['tariff_id']), None)

    if tariff:
        subscription = db.create_subscription(
            user_id=callback.from_user.id,
            tariff_id=tariff['id'],
            is_trial=False
        )

        expires = datetime.fromisoformat(subscription['expires_at']).strftime("%d.%m.%Y")

        await callback.message.edit_text(
            texts.PAYMENT_SUCCESS.format(
                tariff_name=tariff['name'],
                expires=expires
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


@router.callback_query(F.data == "support")
async def callback_support(callback: CallbackQuery):
    """Поддержка"""
    await callback.message.delete()
    await send_screen(
        callback, "support",
        texts.SUPPORT_INFO,
        kb.get_support_keyboard()
    )
    await callback.answer()


# === Admin Callbacks ===

@router.callback_query(F.data == "admin_stats")
async def callback_admin_stats(callback: CallbackQuery):
    """Статистика админ"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Нет доступа")
        return

    stats = db.get_full_stats()
    await callback.message.edit_text(
        texts.ADMIN_STATS.format(
            total_users=stats['total_users'],
            total_trials=stats['total_trials'],
            total_subscriptions=stats['total_subscriptions'],
            active_subs=stats['active_subscriptions'],
            daily_new=stats['daily_new'],
            weekly_new=stats['weekly_new'],
            monthly_new=stats['monthly_new']
        ),
        parse_mode=ParseMode.HTML,
        reply_markup=kb.get_admin_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "admin_broadcast")
async def callback_admin_broadcast(callback: CallbackQuery):
    """Рассылка"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Нет доступа")
        return

    await callback.message.edit_text(
        texts.ADMIN_BROADCAST_INFO,
        parse_mode=ParseMode.HTML,
        reply_markup=kb.get_back_admin_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "admin_back")
async def callback_admin_back(callback: CallbackQuery):
    """Возврат в админ-панель"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Нет доступа")
        return

    await callback.message.edit_text(
        texts.ADMIN_PANEL,
        parse_mode=ParseMode.HTML,
        reply_markup=kb.get_admin_menu()
    )
    await callback.answer()


# === Уведомления ===

async def check_subscriptions_and_notify(bot):
    """Проверяет подписки и отправляет уведомления"""
    try:
        users = db.get_all_users()

        for user_data in users:
            user_id = user_data.get('user_id')
            subscription = db.get_subscription(user_id)

            if not subscription:
                # Проверяем, был ли пробный период и истёк ли он
                if user_data.get('trials_used', 0) >= 1:
                    # Проверяем, отправляли ли уже уведомление об истечении
                    last_expired_notify = user_data.get('last_expired_notify', False)
                    if not last_expired_notify:
                        try:
                            await bot.send_message(
                                user_id,
                                texts.NOTIFICATION_EXPIRED,
                                parse_mode=ParseMode.HTML,
                                reply_markup=kb.get_expired_notification_keyboard()
                            )
                            db.mark_expired_notification_sent(user_id)
                        except Exception as e:
                            logger.error(f"Failed to send expired notification to {user_id}: {e}")
                continue

            # Для активных подписок
            expires_at = datetime.fromisoformat(subscription['expires_at'])
            now = datetime.now()
            days_left = (expires_at - now).days

            # Уведомление за 1 день до окончания
            if days_left == 1:
                last_notified = subscription.get('last_notification')
                if not last_notified or (now - datetime.fromisoformat(last_notified)).days >= 1:
                    try:
                        await bot.send_message(
                            user_id,
                            texts.NOTIFICATION_EXPIRE_SOON,
                            parse_mode=ParseMode.HTML,
                            reply_markup=kb.get_expiring_notification_keyboard()
                        )
                        db.update_subscription_notification(user_id)
                    except Exception as e:
                        logger.error(f"Failed to send expiring notification to {user_id}: {e}")

    except Exception as e:
        logger.error(f"Error in check_subscriptions_and_notify: {e}")


async def notification_scheduler(bot):
    """Фоновый планировщик уведомлений"""
    while True:
        try:
            await check_subscriptions_and_notify(bot)
        except Exception as e:
            logger.error(f"Scheduler error: {e}")

        # Проверяем каждые 6 часов
        await asyncio.sleep(6 * 60 * 60)
