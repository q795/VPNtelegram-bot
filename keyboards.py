"""
Клавиатуры бота
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import TARIFFS, DEMO_SERVERS


def get_main_menu() -> InlineKeyboardMarkup:
    """Главное меню"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="📋 Мой профиль", callback_data="profile"),
        InlineKeyboardButton(text="🔗 Получить VPN", callback_data="get_vpn")
    )

    builder.row(
        InlineKeyboardButton(text="🖥 Серверы", callback_data="servers"),
        InlineKeyboardButton(text="📊 Статистика", callback_data="stats")
    )

    builder.row(
        InlineKeyboardButton(text="💳 Тарифы", callback_data="tariffs"),
        InlineKeyboardButton(text="📖 Помощь", callback_data="help")
    )

    return builder.as_markup()


def get_profile_keyboard(has_subscription: bool, is_trial: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура профиля"""
    builder = InlineKeyboardBuilder()

    if has_subscription:
        builder.row(
            InlineKeyboardButton(text="📱 QR-код", callback_data="qr_code"),
            InlineKeyboardButton(text="🔄 Сменить сервер", callback_data="change_server")
        )
        builder.row(
            InlineKeyboardButton(text="📥 Скачать конфиг", callback_data="download_config")
        )
        if not is_trial:
            builder.row(
                InlineKeyboardButton(text="💎 Продлить подписку", callback_data="renew")
            )
    else:
        builder.row(
            InlineKeyboardButton(text="🧪 Получить пробную версию", callback_data="trial")
        )
        builder.row(
            InlineKeyboardButton(text="💳 Купить подписку", callback_data="tariffs")
        )

    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")
    )

    return builder.as_markup()


def get_tariffs_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура тарифов"""
    builder = InlineKeyboardBuilder()

    for tariff in TARIFFS:
        price_text = f"{tariff['price']}₽"
        if tariff.get("discount"):
            price_text += f" (-{tariff['discount']}%)"

        builder.row(
            InlineKeyboardButton(
                text=f"{tariff['name']} - {price_text}",
                callback_data=f"buy_{tariff['id']}"
            )
        )

    builder.row(
        InlineKeyboardButton(text="🧪 Бесплатный пробный", callback_data="trial")
    )

    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")
    )

    return builder.as_markup()


def get_servers_keyboard(selected_server: int = None) -> InlineKeyboardMarkup:
    """Клавиатура выбора сервера"""
    builder = InlineKeyboardBuilder()

    for server in DEMO_SERVERS:
        marker = "✅ " if server["id"] == selected_server else ""
        builder.row(
            InlineKeyboardButton(
                text=f"{marker}{server['name']}",
                callback_data=f"server_{server['id']}"
            )
        )

    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")
    )

    return builder.as_markup()


def get_back_keyboard() -> InlineKeyboardMarkup:
    """Кнопка назад"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")
    )
    return builder.as_markup()


def get_confirm_trial_keyboard() -> InlineKeyboardMarkup:
    """Подтверждение пробного периода"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Да, получить", callback_data="confirm_trial"),
        InlineKeyboardButton(text="❌ Нет", callback_data="back_to_menu")
    )
    return builder.as_markup()


def get_demo_payment_keyboard(payment_id: str) -> InlineKeyboardMarkup:
    """Демо-кнопка оплаты"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Подтвердить оплату (Демо)",
            callback_data=f"demo_pay_{payment_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Отмена", callback_data="back_to_menu")
    )
    return builder.as_markup()
