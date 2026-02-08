from aiogram.filters import BaseFilter
from aiogram.types import Message

class KnownUser(BaseFilter):
    async def __call__(self, message: Message, db: dict) -> bool:
        print(message.from_user.id)
        print(db)
        # Проверяем наличие пользователя в постоянной базе данных
        user = db['get_user'](message.from_user.id)
        return user is not None