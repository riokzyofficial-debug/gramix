from gramix import Bot, Dispatcher, Router
from gramix.env import load_env
import logging

logging.basicConfig(level=logging.INFO)
load_env()

bot = Bot()
rt  = Router()
dp  = Dispatcher(bot)


@dp.middleware
def logger(msg, next):
    logging.info("[%d] %s", msg.from_user.id, msg.text)
    next()


@rt.message("/start")
def on_start(msg):
    msg.reply("Привет!")


@rt.message()
def echo(msg):
    msg.reply(msg.text)


dp.include(rt)

if __name__ == "__main__":
    dp.run()
