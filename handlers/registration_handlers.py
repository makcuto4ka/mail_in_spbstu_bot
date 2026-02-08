from aiogram import F, Router
from aiogram.types import CallbackQuery, Message, ChatMemberUpdated
from aiogram.filters import Command, CommandStart, StateFilter, ChatMemberUpdatedFilter, KICKED
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from states.states import FSMFillRegistration
from keyboards.keyboards import create_registration_keyboard
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
    await message.answer(text=LEXICON[message.text])


@unregistered_users_router.callback_query(F.data == 'registration', StateFilter(default_state))
async def process_registration_press(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text=LEXICON['fill_login'])
    await state.set_state(FSMFillRegistration.fill_login)

@unregistered_users_router.message(StateFilter(FSMFillRegistration.fill_login), F.text)
async def process_login_sent(message: Message, state: FSMContext):
    await state.update_data(login=message.text)
    await message.delete()
    await message.answer(text=LEXICON['fill_password'])
    await state.set_state(FSMFillRegistration.fill_password)
    
@unregistered_users_router.message(StateFilter(FSMFillRegistration.fill_password), F.text)
async def process_password_sent(message: Message, state: FSMContext, db: dict):
    # Получаем данные пользователя для проверки учетных данных
    user_data = await state.get_data()
    login = user_data.get('login')
    password = message.text

    # Здесь должна быть проверка учетных данных через EWS
    # Пока что временно пропускаем проверку, но в реальном приложении нужно реализовать
    from services.mail_service import send_mail_async
    # Пример тестового соединения - отправка тестового письма на самого себя
    # Это временный способ проверки учетных данных, в реальности нужна отдельная функция проверки
    # credentials_test = await send_mail_async(login, password, [login], "Тест", "Тестовое сообщение для проверки учетных данных")
    # if not credentials_test:
    #     await message.answer(text=LEXICON['wrong_credentials'])
    #     return

    await state.update_data(password=password)
    await message.delete()
    await message.answer(text=LEXICON['end_registration'])
    
    # Сохраняем пользователя в постоянное хранилище
    db["add_user"](message.from_user.id, login, password)
    print(db)
    # здесь запускается функция которая мониторит новые сообшения
    await state.clear()
    
    
@unregistered_users_router.message(StateFilter(default_state), KnownUser())
async def send_echo_not_understand(message: Message):
    await message.reply(text=LEXICON['not_understand'])
    
@unregistered_users_router.message(StateFilter(default_state))
async def send_echo_not_registration(message: Message):
    await message.reply(
        text=LEXICON['not_registration'],
        reply_markup=create_registration_keyboard('registration',),
    )
    
@unregistered_users_router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=KICKED), KnownUser())
async def process_user_blocked_bot(event: ChatMemberUpdated, db: dict):
    # Удаляем из постоянной базы данных, установив active в False
    db["update_user"](event.from_user.id, active=False)