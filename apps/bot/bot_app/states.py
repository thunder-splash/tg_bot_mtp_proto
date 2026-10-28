from aiogram.fsm.state import State, StatesGroup


class BuyStates(StatesGroup):
    choosing_plan = State()
    waiting_channel = State()


class AdminStates(StatesGroup):
    waiting_proxy_url = State()
    waiting_credit_order = State()
