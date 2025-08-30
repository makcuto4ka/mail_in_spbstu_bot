from aiogram.fsm.state import State, StatesGroup


class FSMFillRegistration(StatesGroup):
    fill_login = State()
    fill_password = State()
    

