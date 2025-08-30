from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from states.registration_status import FSMFillRegistration
from keyboards.registration_kb import create_registration_keyboard
from filters.filters import KnownUser
from lexicon.lexicon import LEXICON


unregistered_users_router = Router()


# Этот хэндлер будет срабатывать на команду "/start" -
@unregistered_users_router.message(CommandStart(), StateFilter(default_state))
async def process_start_command(message: Message):
    await message.answer(
        text=LEXICON[message.text],
        reply_markup=create_registration_keyboard('registration',),
        )


# Этот хэндлер будет срабатывать на команду "/help"
@unregistered_users_router.message(Command(commands="help"), StateFilter(default_state))
async def process_help_command(message: Message):
    await message.answer(LEXICON[message.text])


@unregistered_users_router.callback_query(F.data == 'registration', StateFilter(default_state))
async def process_registration_press(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(LEXICON['fill_login'])
    await state.set_state(FSMFillRegistration.fill_login)

@unregistered_users_router.message(StateFilter(FSMFillRegistration.fill_login), F.text)
async def process_login_sent(message: Message, state: FSMContext):
    await state.update_data(login=message.text)
    await message.delete()
    await message.answer(LEXICON['fill_password'])
    await state.set_state(FSMFillRegistration.fill_password)
    
@unregistered_users_router.message(StateFilter(FSMFillRegistration.fill_password), F.text)
async def process_login_sent(message: Message, state: FSMContext, db: dict):
    await state.update_data(password=message.text)
    await message.delete()
    await message.answer(LEXICON['end_registration'])
    db["users"][message.from_user.id] = await state.get_data()
    print(db)
    await state.clear()

@unregistered_users_router.message(StateFilter(default_state), KnownUser())
async def send_echo(message: Message):
    await message.reply(LEXICON[''])
    
@unregistered_users_router.message(StateFilter(default_state), KnownUser())
async def send_echo(message: Message):
    await message.reply(text='Извините, моя твоя не понимать')