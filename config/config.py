from dataclasses import dataclass
from environs import Env


@dataclass
class TgBot:
    token: str  # Токен для доступа к телеграм-боту


@dataclass
class MailSettings:
    server: str
    port: int
    verify_ssl: bool = True


@dataclass
class PollerSettings:
    slot_seconds: int


@dataclass
class LogSettings:
    level: str
    format: str


@dataclass
class Config:
    bot: TgBot
    mail: MailSettings
    poller: PollerSettings
    log: LogSettings


def load_config(path: str | None = None) -> Config:
    env = Env()
    env.read_env(path)
    return Config(
        bot=TgBot(token=env("BOT_TOKEN")),
        mail=MailSettings(
            server=env("MAIL_SERVER", "mail.spbstu.ru"),
            port=env.int("MAIL_PORT", 443),
            verify_ssl=env.bool("DEFAULT_VERIFY_SSL", True)
        ),
        poller=PollerSettings(
            slot_seconds=env.int("POLL_SLOT_SECONDS", 300)
        ),
        log=LogSettings(
            level=env("LOG_LEVEL", "INFO"),
            format=env("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
    )