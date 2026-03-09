from gramix import Bot, Dispatcher, Router, SQLiteStorage, State, Step
from gramix.env import load_env

load_env()

bot = Bot()
rt  = Router(storage=SQLiteStorage("states.db"))
dp  = Dispatcher(bot)


class Form(State):
    name = Step()
    age  = Step()
    city = Step()


@rt.message("/start")
def on_start(msg):
    msg.reply("Привет! Напиши /reg чтобы зарегистрироваться.")


@rt.message("/reg")
def on_reg(msg):
    state = rt.fsm.get(msg.from_user.id)
    state.set(Form.name)
    msg.reply("Как тебя зовут?")


@rt.state(Form.name)
def get_name(msg, state):
    state.data["name"] = msg.text.strip()
    state.next()
    msg.reply("Сколько лет?")


@rt.state(Form.age)
def get_age(msg, state):
    if not msg.text.isdigit():
        msg.reply("Введи число:")
        return
    state.data["age"] = int(msg.text)
    state.next()
    msg.reply("Из какого города?")


@rt.state(Form.city)
def get_city(msg, state):
    state.data["city"] = msg.text.strip()
    name = state.data["name"]
    age  = state.data["age"]
    city = state.data["city"]
    state.finish()
    msg.reply(f"Готово!\n\nИмя: {name}\nВозраст: {age}\nГород: {city}")


@rt.message("/cancel")
def on_cancel(msg):
    state = rt.fsm.get(msg.from_user.id)
    if state.is_active:
        state.finish()
        msg.reply("Отменено.")
    else:
        msg.reply("Нечего отменять.")


dp.include(rt)

if __name__ == "__main__":
    dp.run()
