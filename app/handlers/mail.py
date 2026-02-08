"""
app/handlers/mail.py

Хендлеры для команд и уведомлений, связанных с почтой
"""
import logging
from typing import Dict, Any

from aiogram import Bot

from lexicon.lexicon import LEXICON
from config.config import load_config

logger = logging.getLogger(__name__)
config = load_config()


async def notify_user_new_email(telegram_id: int, mail_dict: Dict[str, Any], bot: Bot):
    """Отправляет уведомление пользователю о новом письме"""
    try:
        # Формируем сообщение о новом письме
        message_text = f"📧 Новое письмо:\n\n" \
                      f"От: {mail_dict.get('from', 'Неизвестно')}\n" \
                      f"Тема: {mail_dict.get('subject', 'Без темы')}\n" \
                      f"Дата получения: {mail_dict.get('datetime_received', 'Неизвестна')}\n"
        
        if mail_dict.get('has_attachments'):
            attachments_info = ", ".join([att.get('name', 'Неизвестно') for att in mail_dict.get('attachments', [])])
            message_text += f"Вложения: {attachments_info}\n"
        
        await bot.send_message(telegram_id, message_text)
        logger.info(f"Notification sent to user {telegram_id}: {message_text}")
    except Exception as e:
        logger.error(f"Error sending notification to user {telegram_id}: {e}")


# Здесь также должны быть обработчики для команды проверки почты
# def register_mail_handlers(dp: Dispatcher):
#     dp.message.register(check_mail_handler, Command("check_mail"))
