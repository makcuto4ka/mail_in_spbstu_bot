"""
app/tasks/poller.py

Централизованный round-robin poller для проверки почты пользователей
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

# Удаляем импорт специфичных исключений из exchangelib, так как они могут отличаться в разных версиях
# from exchangelib import ErrorServerBusy

from services.mail_service import fetch_unread_emails_async
from config.config import Config, load_config
from database.database import init_db

logger = logging.getLogger(__name__)


class Poller:
    def __init__(self, db: Dict[str, Any], config: Config, bot=None):
        self.db = db
        self.config = config
        self.bot = bot
        self.running = False

    async def poll_loop(self):
        """Основной цикл опроса почты пользователей"""
        logger.info("Starting poller loop")
        self.running = True

        while self.running:
            try:
                # Находим пользователя с минимальным next_poll_at
                user_to_poll = await self._get_next_user_to_poll()
                if user_to_poll is None:
                    # Нет активных пользователей, ждем перед следующей проверкой
                    await asyncio.sleep(10)  # ждем 10 секунд перед следующей проверкой
                    continue

                telegram_id, user_data = user_to_poll

                # Проверяем, пришло ли время опроса
                now = datetime.utcnow()
                if user_data["next_poll_at"] > now:
                    # Ждем до наступления времени опроса
                    sleep_time = (user_data["next_poll_at"] - now).total_seconds()
                    await asyncio.sleep(sleep_time)

                # Обновляем next_poll_at до запроса, чтобы избежать двойного опроса
                active_users_count = await self._get_active_users_count()
                next_poll_time = now + timedelta(seconds=self.config.poller.slot_seconds * active_users_count)
                self.db["update_user"](telegram_id, next_poll_at=next_poll_time)

                # Получаем непрочитанные письма
                try:
                    emails = await fetch_unread_emails_async(
                        email=user_data["login"],
                        password=user_data["password"],
                        server=self.config.mail.server,
                        verify_ssl=self.config.mail.verify_ssl
                    )

                    if emails:
                        # Отправляем уведомления о новых письмах
                        from app.handlers.mail import notify_user_new_email
                        for email_data in emails:
                            if self.bot:
                                await notify_user_new_email(telegram_id, email_data, self.bot)
                            else:
                                logger.warning(f"Bot not available, cannot send notification to user {telegram_id}")

                        # Сброс ошибок при успешном опросе
                        self.db["update_user"](telegram_id, poll_failures=0)
                        logger.info(f"Found {len(emails)} new emails for user {telegram_id}")

                except Exception as e:
                    # Обработка ошибок EWS, включая ошибки ограничения частоты
                    logger.warning(f"EWS error for user {telegram_id}: {e}")
                    # Проверяем, является ли ошибка ошибкой ограничения частоты
                    if "rate" in str(e).lower() or "throttle" in str(e).lower() or "limit" in str(e).lower() or "429" in str(e):
                        # Обработка ошибки ограничения частоты
                        backoff_seconds = 300  # 5 минут по умолчанию для rate limit
                        logger.info(f"Rate limit detected for user {telegram_id}, applying {backoff_seconds}s backoff")
                    else:
                        # Обработка других ошибок с экспоненциальным backoff
                        current_failures = user_data.get("poll_failures", 0)
                        backoff_seconds = min(300 * (2 ** current_failures), 3600) # Экспоненциальный backoff, максимум 1 час
                        logger.info(f"Other error for user {telegram_id}, applying {backoff_seconds}s backoff with failure count {current_failures + 1}")
                    
                    next_poll_time = now + timedelta(seconds=backoff_seconds)
                    current_failures = user_data.get("poll_failures", 0)
                    self.db["update_user"](
                        telegram_id,
                        next_poll_at=next_poll_time,
                        poll_failures=current_failures + 1
                    )

            except Exception as e:
                logger.error(f"Unexpected error in poll loop: {e}")
                await asyncio.sleep(10)  # Ждем перед следующей итерацией при ошибке

    async def _get_next_user_to_poll(self):
        """Находит пользователя с минимальным next_poll_at"""
        now = datetime.utcnow()
        next_user = None
        min_next_poll_at = None

        for telegram_id in self.db["get_all_user_ids"]():
            user_data = self.db["get_user"](telegram_id)
            if not user_data.get("active", False):
                continue

            next_poll_at = user_data.get("next_poll_at")
            if next_poll_at and (min_next_poll_at is None or next_poll_at < min_next_poll_at):
                min_next_poll_at = next_poll_at
                next_user = (telegram_id, user_data)

        return next_user

    async def _get_active_users_count(self):
        """Возвращает количество активных пользователей"""
        count = 0
        for telegram_id in self.db["get_all_user_ids"]():
            user_data = self.db["get_user"](telegram_id)
            if user_data and user_data.get("active", False):
                count += 1
        return count

    def stop(self):
        """Останавливает poller"""
        self.running = False
