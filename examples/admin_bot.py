from gramix import Bot, Dispatcher, Router
from gramix.env import load_env

load_env()

ADMINS = {123456789}

bot = Bot()
rt  = Router()
dp  = Dispatcher(bot)


def is_admin(msg) -> bool:
    return msg.from_user.id in ADMINS


@rt.message("/start")
def on_start(msg):
    msg.reply("Бот запущен.")


@rt.message("/ban")
def on_ban(msg):
    if not is_admin(msg):
        msg.reply("Нет доступа.")
        return
    if not msg.reply_to_message:
        msg.reply("Ответь на сообщение пользователя.")
        return
    user_id = msg.reply_to_message.from_user.id
    bot.ban_chat_member(msg.chat.id, user_id)
    msg.reply(f"Пользователь {user_id} заблокирован.")


@rt.message("/unban")
def on_unban(msg):
    if not is_admin(msg):
        msg.reply("Нет доступа.")
        return
    if not msg.reply_to_message:
        msg.reply("Ответь на сообщение пользователя.")
        return
    user_id = msg.reply_to_message.from_user.id
    bot.unban_chat_member(msg.chat.id, user_id)
    msg.reply(f"Пользователь {user_id} разблокирован.")


@rt.message("/mute")
def on_mute(msg):
    if not is_admin(msg):
        msg.reply("Нет доступа.")
        return
    if not msg.reply_to_message:
        msg.reply("Ответь на сообщение пользователя.")
        return
    user_id = msg.reply_to_message.from_user.id
    bot.restrict_chat_member(msg.chat.id, user_id, permissions={
        "can_send_messages": False,
        "can_send_media_messages": False,
        "can_send_polls": False,
        "can_send_other_messages": False,
    })
    msg.reply(f"Пользователь {user_id} замьючен.")


@rt.message("/unmute")
def on_unmute(msg):
    if not is_admin(msg):
        msg.reply("Нет доступа.")
        return
    if not msg.reply_to_message:
        msg.reply("Ответь на сообщение пользователя.")
        return
    user_id = msg.reply_to_message.from_user.id
    bot.restrict_chat_member(msg.chat.id, user_id, permissions={
        "can_send_messages": True,
        "can_send_media_messages": True,
        "can_send_polls": True,
        "can_send_other_messages": True,
    })
    msg.reply(f"Пользователь {user_id} размьючен.")


dp.include(rt)

if __name__ == "__main__":
    dp.run()
