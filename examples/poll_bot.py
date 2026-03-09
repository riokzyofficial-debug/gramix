from gramix import (
    Bot, Dispatcher, Router,
    Poll, PollAnswer,
    F,
    ParseMode,
    load_env,
)

load_env()

bot = Bot(parse_mode=ParseMode.HTML)
dp  = Dispatcher(bot)
rt  = Router()
dp.include(rt)


@rt.message("/start")
def on_start(msg):
    msg.answer(
        "<b>gramix Polls Demo</b>\n\n"
        "/poll — anonymous regular poll\n"
        "/multipoll — multi-choice non-anonymous poll\n"
        "/quiz — quiz with correct answer\n"
        "/timedpoll — poll that closes in 60 seconds\n"
        "/stoppoll — reply to a poll to close it"
    )


@rt.message("/poll")
def send_regular_poll(msg):
    bot.send_poll(
        chat_id=msg.chat.id,
        question="What is your favourite programming language?",
        options=["Python", "TypeScript", "Rust", "Go", "Other"],
        is_anonymous=True,
    )


@rt.message("/multipoll")
def send_multi_poll(msg):
    bot.send_poll(
        chat_id=msg.chat.id,
        question="Which frameworks do you use? (choose all that apply)",
        options=["FastAPI", "Django", "Flask", "aiohttp", "None"],
        is_anonymous=False,
        allows_multiple_answers=True,
    )


@rt.message("/quiz")
def send_quiz(msg):
    bot.send_poll(
        chat_id=msg.chat.id,
        question="What does GIL stand for in CPython?",
        options=[
            "Global Import Loader",
            "General Interpreter Lock",
            "Global Interpreter Lock",
            "Garbage Index Layer",
        ],
        poll_type="quiz",
        correct_option_id=2,
        explanation=(
            "The <b>Global Interpreter Lock</b> is a mutex in CPython that "
            "allows only one thread to execute Python bytecode at a time."
        ),
        is_anonymous=True,
    )


@rt.message("/timedpoll")
def send_timed_poll(msg):
    bot.send_poll(
        chat_id=msg.chat.id,
        question="Quick vote — tabs or spaces?",
        options=["Tabs", "Spaces", "Both (chaos)"],
        open_period=60,
        is_anonymous=True,
    )


@rt.message("/stoppoll")
def cmd_stop_poll(msg):
    if not msg.reply_to_message:
        msg.answer("Reply to a poll message with /stoppoll.")
        return
    if not msg.reply_to_message.poll:
        msg.answer("The replied message does not contain a poll.")
        return
    poll = bot.stop_poll(
        chat_id=msg.chat.id,
        message_id=msg.reply_to_message.message_id,
    )
    msg.answer(f"Poll closed. Final total: <b>{poll.total_voter_count}</b> votes.")


@rt.poll_answer()
def on_poll_answer(answer: PollAnswer):
    if answer.user is None:
        return
    name = answer.user.full_name
    if answer.retracted:
        bot.send_message(
            answer.user.id,
            f"You retracted your vote in poll <code>{answer.poll_id}</code>.",
        )
        return
    chosen = ", ".join(f"option #{i}" for i in answer.option_ids)
    bot.send_message(
        answer.user.id,
        f"Thanks, <b>{name}</b>! You picked: {chosen}.",
    )


@rt.message(F.quiz)
def on_quiz_message(msg):
    poll = msg.poll
    correct = poll.options[poll.correct_option_id].text if poll.correct_option_id is not None else "?"
    msg.answer(
        f"Forwarded quiz: <b>{poll.question}</b>\n"
        f"Correct answer: <b>{correct}</b>"
    )


@rt.message(F.poll)
def on_poll_message(msg):
    poll = msg.poll
    status = "closed" if poll.is_closed else "open"
    kind   = "quiz" if poll.poll_type == "quiz" else "poll"
    msg.answer(
        f"Forwarded {kind} (<i>{status}</i>): <b>{poll.question}</b>\n"
        f"Total votes: {poll.total_voter_count}"
    )


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    dp.run()
