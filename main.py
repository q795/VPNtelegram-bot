"""
VPN Telegram Bot - Точка входа
"""
import asyncio
import logging
import sys
import os

# Добавляем путь к модулям
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from bot import router

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Главная функция запуска бота"""

    # Создаём бота
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    # Создаём диспетчер
    dp = Dispatcher()

    # Регистрируем роутер
    dp.include_router(router)

    # Удаляем вебхук если есть
    await bot.delete_webhook(drop_pending_updates=True)

    logger.info("🚀 VPN Бот запускается...")

    try:
        # Запускаем polling
        await dp.start_polling(
            bot,
            allowed_updates=['message', 'callback_query']
        )
    finally:
        # Закрываем соединение
        await bot.session.close()
        logger.info("👋 Бот остановлен")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        raise
