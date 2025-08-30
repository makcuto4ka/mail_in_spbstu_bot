from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from lexicon.lexicon import LEXICON



def create_registration_keyboard(button: str) -> InlineKeyboardMarkup:
    registration_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=LEXICON[button],
                    callback_data=button,
                )
            ]
        ]
    )
    return registration_keyboard