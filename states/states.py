from aiogram.fsm.state import State, StatesGroup


class FSMFillRegistration(StatesGroup):
    fill_login = State()
    fill_password = State()
    

class FSMFillEmail(StatesGroup):
    fill_form = State()
    fill_addressees = State()
    fill_topic = State()
    fill_text_massage = State()
    upload_attachment = State()
    sending_email = State()
    