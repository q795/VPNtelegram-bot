"""
Клавиатуры бота VERA VPN
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import TARIFFS, DEMO_SERVERS, SUPPORT_USERNAME, USER_AGREEMENT_URL, PRIVACY_POLICY_URL


def get_main_menu(has_trial_used: bool = False, has_active_subscription: bool = False) -> InlineKeyboardMarkup:
    """Главное меню - динамическое"""
    builder = InlineKeyboardBuilder()

    # Пробный период виден только если ещё не использовал
    if not has_trial_used:
        builder.row(
            InlineKeyboardButton(text="🎁 Активировать пробный период", callback_data="trial")
        )

    builder.row(
        InlineKeyboardButton(text="🛡 Подключить VPN", callback_data="tariffs")
    )

    builder.row(
        InlineKeyboardButton(text="🔐 Мои ключи", callback_data="download_config"),
        InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile")
    )

    builder.row(
        InlineKeyboardButton(text="💬 Поддержка", callback_data="support")
    )

    return builder.as_markup()


def get_tariffs_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура тарифов"""
    builder = InlineKeyboardBuilder()

    for tariff in TARIFFS:
        # Формируем текст с ценой и скидкой за месяц
        price_text = f"{tariff['price']}₽"
        if tariff.get('monthly_price'):
            price_text += f" ({tariff['monthly_price']}₽/мес)"

        builder.row(
            InlineKeyboardButton(
                text=f"{tariff['name']} — {price_text}",
                callback_data=f"buy_{tariff['id']}"
            )
        )

    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")
    )

    return builder.as_markup()


def get_profile_keyboard(has_subscription: bool, is_trial: bool = False, trial_used: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура профиля"""
    builder = InlineKeyboardBuilder()

    if has_subscription:
        # Есть подписка - кнопка "Мои ключи"
        builder.row(
            InlineKeyboardButton(text="🔐 Мои ключи", callback_data="download_config")
        )
    else:
        # Нет подписки - кнопка "Подключить VPN"
        builder.row(
            InlineKeyboardButton(text="💎 Подключить VPN", callback_data="tariffs")
        )

    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")
    )

    return builder.as_markup()


def get_trial_success_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура после активации пробного"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔐 Мои ключи", callback_data="download_config")
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
        InlineKeyboardButton(text="✅ Активировать", callback_data="confirm_trial"),
        InlineKeyboardButton(text="🔙 Отмена", callback_data="back_to_menu")
    )
    return builder.as_markup()


def get_demo_payment_keyboard(tariff_id: str) -> InlineKeyboardMarkup:
    """Демо-кнопка оплаты"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Подтвердить оплату",
            callback_data=f"demo_pay_{tariff_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Отмена", callback_data="back_to_menu")
    )
    return builder.as_markup()


def get_support_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура поддержки"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="📱 Написать в поддержку",
            url=f"https://t.me/{SUPPORT_USERNAME}"
        )
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")
    )
    return builder.as_markup()


def get_expiring_notification_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура уведомления об окончании"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💎 Продлить VPN", callback_data="tariffs")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")
    )
    return builder.as_markup()


def get_expired_notification_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура когда подписка истекла"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💎 Подключить VPN", callback_data="tariffs")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")
    )
    return builder.as_markup()


def get_profile_links_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с ссылками на документы"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="📄 Пользовательское соглашение",
            url=USER_AGREEMENT_URL
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🔒 Политика конфиденциальности",
            url=PRIVACY_POLICY_URL
        )
    )
    return builder.as_markup()


# ==========================================
# АДМИН-ПАНЕЛЬ
# ==========================================
def get_admin_menu() -> InlineKeyboardMarkup:
    """Главное меню админ-панели"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")
    )
    builder.row(
        InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")
    )
    builder.row(
        InlineKeyboardButton(text="💎 Тарифы", callback_data="admin_tariffs")
    )
    builder.row(
        InlineKeyboardButton(text="👥 Люди", callback_data="admin_users")
    )
    builder.row(
        InlineKeyboardButton(text="🌐 Серверы", callback_data="admin_servers")
    )
    builder.row(
        InlineKeyboardButton(text="👮 Права админа", callback_data="admin_admins")
    )
    builder.row(
        InlineKeyboardButton(text="⚙️ Настройки", callback_data="admin_settings")
    )

    builder.row(
        InlineKeyboardButton(text="🔙 Выход", callback_data="back_to_menu")
    )

    return builder.as_markup()


def get_admin_tariffs_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура управления тарифами"""
    builder = InlineKeyboardBuilder()

    for tariff in TARIFFS:
        builder.row(
            InlineKeyboardButton(
                text=f"{tariff['name']} — {tariff['price']}₽",
                callback_data=f"admin_edit_tariff_{tariff['id']}"
            )
        )

    builder.row(
        InlineKeyboardButton(text="➕ Добавить тариф", callback_data="admin_add_tariff")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")
    )

    return builder.as_markup()


def get_admin_users_keyboard(page: int = 1) -> InlineKeyboardMarkup:
    """Клавиатура списка пользователей"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="📥 Экспорт CSV", callback_data="admin_export_users")
    )
    builder.row(
        InlineKeyboardButton(text="🔍 Поиск", callback_data="admin_search_user")
    )

    builder.row(
        InlineKeyboardButton(text="◀ Назад", callback_data=f"admin_users_p{page-1}" if page > 1 else "admin_menu"),
        InlineKeyboardButton(text="Вперёд ▶", callback_data=f"admin_users_p{page+1}")
    )

    builder.row(
        InlineKeyboardButton(text="🔙 В меню", callback_data="admin_menu")
    )

    return builder.as_markup()


def get_admin_broadcast_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура рассылки"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="📷 С фото", callback_data="admin_broadcast_photo")
    )
    builder.row(
        InlineKeyboardButton(text="📝 Только текст", callback_data="admin_broadcast_text")
    )

    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")
    )

    return builder.as_markup()


def get_admin_servers_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура управления серверами"""
    builder = InlineKeyboardBuilder()

    for server in DEMO_SERVERS:
        status = "🟢" if not server.get('offline') else "🔴"
        builder.row(
            InlineKeyboardButton(
                text=f"{status} {server['name']}",
                callback_data=f"admin_edit_server_{server['id']}"
            )
        )

    builder.row(
        InlineKeyboardButton(text="➕ Добавить сервер", callback_data="admin_add_server")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")
    )

    return builder.as_markup()


def get_admin_back_keyboard() -> InlineKeyboardMarkup:
    """Кнопка назад в админке"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")
    )
    return builder.as_markup()