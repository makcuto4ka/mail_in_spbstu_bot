from aiogram.filters import BaseFilter
from aiogram.types import Message

class KnownUser(BaseFilter):
    async def __call__(self, massage: Message, db: dict) -> bool:
        print(massage.from_user.id)
        print(db)
        return massage.from_user.id in db['users']