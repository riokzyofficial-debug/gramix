from gramix import Bot, Dispatcher, Router, State, Step
from gramix.env import load_env

load_env()

bot = Bot()
rt  = Router()
dp  = Dispatcher(bot)


class Registration(State):
    name = Step()
    age  = Step()
    city = Step()


@rt.message("/start")
def on_start(msg):
    msg.reply("Привет! Напиши /reg чтобы зарегистрироваться или /cancel для отмены.")


@rt.message("/reg")
def on_reg(msg):
    state = rt.fsm.get(msg.from_user.id)
    state.set(Registration.name)
    msg.reply("Как тебя зовут?")


@rt.state(Registration.name)
def get_name(msg, state):
    if not msg.text or len(msg.text) < 2:
        msg.reply("Имя должно быть минимум 2 символа. Попробуй ещё:")
        return
    state.data["name"] = msg.text.strip()
    state.next()
    msg.reply(f"Приятно, {state.data['name']}! Сколько лет?")


@rt.state(Registration.age)
def get_age(msg, state):
    if not msg.text or not msg.text.isdigit():
        msg.reply("Введи возраст числом:")
        return
    age = int(msg.text)
    if not 5 <= age <= 120:
        msg.reply("Введи реальный возраст:")
        return
    state.data["age"] = age
    state.next()
    msg.reply("Из какого ты города?")


@rt.state(Registration.city)
def get_city(msg, state):
    if not msg.text or len(msg.text) < 2:
        msg.reply("Введи название города:")
        return
    state.data["city"] = msg.text.strip()
    name = state.data["name"]
    age  = state.data["age"]
    city = state.data["city"]
    state.finish()
    msg.reply(
        f"Готово!\n\n"
        f"Имя: {name}\n"
        f"Возраст: {age}\n"
        f"Город: {city}"
    )


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
