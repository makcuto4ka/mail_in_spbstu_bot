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

def create_inline_kb(width: int, *args: str, last_btns: list | None = None) -> InlineKeyboardMarkup:
    
    kb_builder = InlineKeyboardBuilder()
    buttons: list[InlineKeyboardButton] = []

    if args:
        for button in args:
            buttons.append(
                InlineKeyboardButton(
                    text=LEXICON[button] if button in LEXICON else button,
                    callback_data=button,
                )
            )

    kb_builder.row(*buttons, width=width)
    if last_btns:
        for button in last_btns:
            kb_builder.row(InlineKeyboardButton(text=LEXICON[button], callback_data=button))

    return kb_builder.as_markup()