"""
app/services/mail_service.py

Функции:
- send_mail(...) -> bool
- fetch_unread_emails(...) -> list[dict]
"""

from typing import List, Optional, Dict, Any
import logging
from pathlib import Path
import asyncio

from exchangelib import (
    Account,
    Credentials,
    Configuration,
    Message,
    FileAttachment,
    DELEGATE,
)
from exchangelib.protocol import BaseProtocol, NoVerifyHTTPAdapter

logger = logging.getLogger(__name__)


def _build_account(email: str, password: str, server: str, verify_ssl: bool = True) -> Account:
    """
    Создаёт и возвращает объект exchangelib.Account.
    Если verify_ssl == False — переключаем адаптер, позволяющий игнорировать валидность сертификата (DEV only).
    """
    creds = Credentials(username=email, password=password)
    config = Configuration(server=server, credentials=creds)

    if not verify_ssl:
        # DEV: отключаем проверку сертификатов (внимание: небезопасно)
        # Альтернативно можно указать config.verify_ssl=False если ваша версия exchangelib это поддерживает.
        BaseProtocol.HTTP_ADAPTER_CLS = NoVerifyHTTPAdapter
        logger.warning("SSL verification disabled for EWS connections (NoVerifyHTTPAdapter).")

    account = Account(
        primary_smtp_address=email,
        config=config,
        autodiscover=False,
        access_type=DELEGATE,
    )
    return account


def send_mail(
    email: str,
    password: str,
    to: List[str],
    subject: str,
    body: str,
    attachments: Optional[List[str]] = None,
    server: str = "mail.spbstu.ru",
    verify_ssl: bool = False,
    save_to_sent: bool = True,
) -> bool:
    """
    Отправляет письмо через EWS (exchangelib).
    :param email: адрес отправителя (учётная запись)
    :param password: пароль / app password
    :param to: список строк с адресами получателей
    :param subject: тема
    :param body: текст тела письма (plain)
    :param attachments: список локальных путей к файлам
    :param server: сервер EWS, по умолчанию "mail.spbstu.ru"
    :param verify_ssl: проверять ли SSL-сертификат (если False — отключит проверку; DEV only)
    :param save_to_sent: сохранять копию в папке Sent
    :return: True при успехе, False при ошибке
    """
    try:
        account = _build_account(email=email, password=password, server=server, verify_ssl=verify_ssl)

        folder = account.sent if save_to_sent else None
        msg = Message(
            account=account,
            folder=folder,
            subject=subject,
            body=body,
            to_recipients=to,
        )

        if attachments:
            for p in attachments:
                path = Path(p)
                if not path.exists():
                    logger.warning("Attachment not found, skipping: %s", p)
                    continue
                content = path.read_bytes()
                msg.attach(FileAttachment(name=path.name, content=content))

        # send_and_save() — отправляет и сохраняет (если folder задан)
        msg.send_and_save()
        logger.info("Email sent: subject=%s to=%s", subject, to)
        return True

    except Exception as exc:
        logger.exception("Failed to send email via EWS: %s", exc)
        return False


def fetch_unread_emails(
    email: str,
    password: str,
    limit: int = 20,
    mark_as_read: bool = False,
    server: str = "mail.spbstu.ru",
    verify_ssl: bool = True,
) -> List[Dict[str, Any]]:
    """
    Получает список непрочитанных писем из INBOX (через exchangelib).
    Возвращает список словарей:
      {
        "id": item.id,
        "subject": item.subject,
        "from": item.sender.email_address if available,
        "datetime_received": item.datetime_received,
        "has_attachments": item.has_attachments,
        "attachments": [ {"name":..., "size":...}, ... ]  # имена и размеры (не скачивает содержимое)
      }
    :param email: адрес электронной почты
    :param password: пароль
    :param limit: максимум N писем (по убыванию datetime_received)
    :param mark_as_read: пометить письма как прочитанные (save() после изменения)
    :param server: сервер EWS, по умолчанию "mail.spbstu.ru"
    :param verify_ssl: отключить проверку сертификата (DEV only)
    """
    out: List[Dict[str, Any]] = []
    try:
        account = _build_account(email=email, password=password, server=server, verify_ssl=verify_ssl)

        # Фильтр непрочитанных писем
        # Сначала применяем only() для ограничения полей, затем slice для ограничения количества
        qs = account.inbox.filter(is_read=False).order_by("-datetime_received").only("subject", "sender", "datetime_received", "has_attachments", "id")[:limit]

        for item in qs:
            entry: Dict[str, Any] = {
                "id": getattr(item, "item_id", None) or getattr(item, "id", None),
                "subject": item.subject,
                "from": (item.sender.email_address if getattr(item, "sender", None) else None),
                "datetime_received": getattr(item, "datetime_received", None),
                "has_attachments": bool(getattr(item, "has_attachments", False)),
                "attachments": [],
            }

            # Если есть вложения — перечислим имена и размеры (не скачиваем содержимое по-умолчанию)
            if item.has_attachments:
                # item.attachments — коллекция вложений
                for att in item.attachments:
                    # FileAttachment имеет атрибут name и size (size может быть отсутствовать)
                    name = getattr(att, "name", None)
                    size = getattr(att, "size", None)
                    entry["attachments"].append({"name": name, "size": size})

            out.append(entry)

            if mark_as_read:
                item.is_read = True
                item.save(update_fields=["is_read"])

        logger.info("Fetched %d unread emails (limit=%d)", len(out), limit)
        return out

    except Exception as exc:
        logger.exception("Failed to fetch unread emails: %s", exc)
        return []


async def send_mail_async(email: str, password: str, to: List[str], subject: str, body: str, attachments: Optional[List[str]] = None, server: str = "mail.spbstu.ru", verify_ssl: bool = False, save_to_sent: bool = True) -> bool:
    return await asyncio.to_thread(send_mail, email, password, to, subject, body, attachments, server, verify_ssl, save_to_sent)

async def fetch_unread_emails_async(email: str, password: str, limit: int = 20, mark_as_read: bool = False, server: str = "mail.spbstu.ru", verify_ssl: bool = True) -> List[Dict[str, Any]]:
    return await asyncio.to_thread(fetch_unread_emails, email, password, limit, mark_as_read, server, verify_ssl)