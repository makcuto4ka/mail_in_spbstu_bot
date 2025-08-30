from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from states.registration_status import FSMFillRegistration
from keyboards.registration_kb import create_registration_keyboard
from lexicon.lexicon import LEXICON
from filters.filters import KnownUser


registered_users_router = Router()

registered_users_router.message.filter(KnownUser())

