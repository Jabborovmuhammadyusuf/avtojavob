from aiogram.fsm.state import State, StatesGroup

class AdminBroadcast(StatesGroup):
    waiting_for_message = State()

class AdminPremium(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_days = State()