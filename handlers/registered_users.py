from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from states.states import FSMFillEmail
from keyboards.keyboards import create_inline_kb
from lexicon.lexicon import LEXICON
from filters.filters import KnownUser
from services.mail_service import send_mail_async


registered_users_router = Router()

registered_users_router.message.filter(KnownUser())

@registered_users_router.message(Command(commands="send_email"), StateFilter(default_state))
async def process_send_email_command(message: Message, state: FSMContext):
    await state.set_state(FSMFillEmail.fill_form)
    await state.update_data(addressees = '', topic = '', text_massage = '', attachment = None)
    await message.answer(
        text=LEXICON[message.text].format(**(await state.get_data())),
        reply_markup=create_inline_kb(2,'but_addressees', 'but_topic', 'but_text_massage', 'but_attachment', last_btns= ['but_send', 'but_cancel']),
        )
    
    
    
    
@registered_users_router.callback_query(F.data == 'but_addressees', StateFilter(FSMFillEmail.fill_form))
async def process_addressees_press(callback: CallbackQuery, state: FSMContext):
    fill_form_msg_id = await callback.message.edit_text(text=LEXICON['addressees'])
    await state.update_data(fill_form_msg_id=fill_form_msg_id.message_id)
    await state.set_state(FSMFillEmail.fill_addressees)

@registered_users_router.message(StateFilter(FSMFillEmail.fill_addressees), F.text)
async def process_addressees_sent(message: Message, state: FSMContext):
    await state.update_data(addressees=message.text.split())
    await message.delete()
    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id= (await state.get_data()).get("fill_form_msg_id") ,
        text=LEXICON['fill_send'].format(**(await state.get_data())),
        reply_markup=create_inline_kb(2,'but_addressees', 'but_topic', 'but_text_massage', 'but_attachment', last_btns= ['but_send', 'but_cancel']),
        )
    await state.set_state(FSMFillEmail.fill_form)
    
    
    
    
@registered_users_router.callback_query(F.data == 'but_topic', StateFilter(FSMFillEmail.fill_form))
async def process_topic_press(callback: CallbackQuery, state: FSMContext):
    fill_form_msg_id = await callback.message.edit_text(text=LEXICON['topic'])
    await state.update_data(fill_form_msg_id=fill_form_msg_id.message_id)
    await state.set_state(FSMFillEmail.fill_topic)
    
@registered_users_router.message(StateFilter(FSMFillEmail.fill_topic), F.text)
async def process_topic_sent(message: Message, state: FSMContext):
    await state.update_data(topic=message.text)
    await message.delete()
    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id= (await state.get_data()).get("fill_form_msg_id") ,
        text=LEXICON['fill_send'].format(**(await state.get_data())),
        reply_markup=create_inline_kb(2,'but_addressees', 'but_topic', 'but_text_massage', 'but_attachment', last_btns= ['but_send', 'but_cancel']),
        )
    await state.set_state(FSMFillEmail.fill_form)
    
    
    
    
@registered_users_router.callback_query(F.data == 'but_text_massage', StateFilter(FSMFillEmail.fill_form))
async def process_text_massage_press(callback: CallbackQuery, state: FSMContext):
    fill_form_msg_id = await callback.message.edit_text(text=LEXICON['text_massage'])
    await state.update_data(fill_form_msg_id=fill_form_msg_id.message_id)
    await state.set_state(FSMFillEmail.fill_text_massage)
    
@registered_users_router.message(StateFilter(FSMFillEmail.fill_text_massage), F.text)
async def process_text_massage_sent(message: Message, state: FSMContext):
    await state.update_data(text_massage=message.text)
    await message.delete()
    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id= (await state.get_data()).get("fill_form_msg_id") ,
        text=LEXICON['fill_send'].format(**(await state.get_data())),
        reply_markup=create_inline_kb(2,'but_addressees', 'but_topic', 'but_text_massage', 'but_attachment', last_btns= ['but_send', 'but_cancel']),
        )
    await state.set_state(FSMFillEmail.fill_form)
    
    
    
    
@registered_users_router.callback_query(F.data == 'but_attachment', StateFilter(FSMFillEmail.fill_form))
async def process_upload_attachment_press(callback: CallbackQuery, state: FSMContext):
    fill_form_msg_id = await callback.message.edit_text(text=LEXICON['attachment'])
    await state.update_data(fill_form_msg_id=fill_form_msg_id.message_id)
    await state.set_state(FSMFillEmail.upload_attachment)
    
@registered_users_router.message(StateFilter(FSMFillEmail.upload_attachment), F.photo | F.video | F.document | F.audio)
async def process_upload_attachment_sent(message: Message, state: FSMContext):
    await state.update_data(attachment=message.document) #Необходимо ппродумать как сохранять любой тип вложения
    await message.delete()
    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id= (await state.get_data()).get("fill_form_msg_id") ,
        text=LEXICON['fill_send'].format(**(await state.get_data())),
        reply_markup=create_inline_kb(2,'but_addressees', 'but_topic', 'but_text_massage', 'but_attachment', last_btns= ['but_send', 'but_cancel']),
        )
    await state.set_state(FSMFillEmail.fill_form)



    
@registered_users_router.callback_query(F.data == 'but_send', StateFilter(FSMFillEmail.fill_form))
async def process_send_email_press(callback: CallbackQuery, state: FSMContext, db: dict):
    # Получаем пользователя из постоянной базы данных
    user_data = db['get_user'](callback.from_user.id)
    if not user_data:
        await callback.message.edit_text(text="Вы не зарегистрированы в системе.")
        await state.clear()
        return

    if (await state.get_data()).get("addressees") != '':
        ok = await send_mail_async(
            email=user_data['login'],
            password=user_data['password'],
            to=(await state.get_data()).get("addressees"),
            subject=(await state.get_data()).get("topic"),
            body=(await state.get_data()).get("text_massage")
        )
        await callback.message.edit_text(
            text=LEXICON["sent" if ok else "error_send"]+'\n\n'+
            LEXICON['fill_send'].format(**(await state.get_data()))+'\n\n'+
            LEXICON["sent" if ok else "error_send"]
        )
        await state.clear()
    
@registered_users_router.callback_query(F.data == 'but_cancel', StateFilter(FSMFillEmail.fill_form))
async def process_cancel_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text=LEXICON['but_cancel'])
    await state.clear()


# Обработчик для команды проверки почты
@registered_users_router.message(Command(commands="check_mail"), StateFilter(default_state))
async def process_check_mail_command(message: Message, db: dict):
    from services.mail_service import fetch_unread_emails_async
    from datetime import datetime
    
    # Получаем пользователя из постоянной базы данных
    user_data = db['get_user'](message.from_user.id)
    if not user_data:
        await message.answer(text="Вы не зарегистрированы в системе.")
        return
    
    # Получаем непрочитанные письма
    emails = await fetch_unread_emails_async(
        email=user_data['login'],
        password=user_data['password'],
        server="mail.spbstu.ru",  # В реальном приложении нужно использовать значение из конфига
        verify_ssl=True
    )
    
    if emails:
        response_text = f"Найдено {len(emails)} непрочитанных писем:\n\n"
        for email in emails[:5]:  # Показываем только первые 5 писем
            subject = email.get('subject', 'Без темы')
            sender = email.get('from', 'Неизвестно')
            date = email.get('datetime_received', 'Неизвестно')
            response_text += f"📧 Тема: {subject}\nОт: {sender}\nДата: {date}\n\n"
    else:
        response_text = "Нет новых писем."
    
    await message.answer(text=response_text)