from gramix import Bot, Dispatcher, Router, InlineQueryResultArticle
from gramix.env import load_env

load_env()

bot = Bot()
rt  = Router()
dp  = Dispatcher(bot)


@rt.message("/start")
def on_start(msg):
    msg.reply("Напиши @botusername запрос чтобы попробовать inline режим.")


@rt.inline()
def on_inline(query):
    text = query.query or "Привет!"
    query.answer([
        InlineQueryResultArticle(
            id="1",
            title=f"Отправить: {text}",
            message_text=text,
            description="Нажми чтобы отправить",
        )
    ])


dp.include(rt)

if __name__ == "__main__":
    dp.run()
