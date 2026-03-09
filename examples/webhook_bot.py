from gramix import Bot, Dispatcher, Router
from gramix.env import load_env

load_env()

bot = Bot()
rt  = Router()
dp  = Dispatcher(bot)


@rt.message("/start")
def on_start(msg):
    msg.reply("Привет!")


@rt.message()
def echo(msg):
    msg.reply(msg.text)


dp.include(rt)

if __name__ == "__main__":
    dp.run(
        webhook=True,
        webhook_url="https://yourdomain.com",
        host="0.0.0.0",
        port=8080,
    )
