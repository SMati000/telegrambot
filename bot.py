import functools
import logging
import os
from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, ConversationHandler, filters

load_dotenv()
PORT = int(os.environ.get('PORT', 5000))

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("TOKEN")

GENDER = range(3)


# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
async def start(update, context) -> int:
    """Starts the conversation and asks the user about their gender."""
    reply_keyboard = [["Boy"], ["Girl"], ["Other"]]

    await update.message.reply_text(
        "Hi! My name is Professor Bot. I will hold a conversation with you. "
        "Send /cancel to stop talking to me.\n\n"
        "Are you a boy or a girl?",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Boy or Girl?"
        ),
    )

    return GENDER


async def gender(update, context) -> int:
    """Stores the selected gender and answers the user."""
    user = update.message.from_user
    logger.info("Gender of %s: %s", user.first_name, update.message.text)
    await update.message.reply_text(
        "I see!", reply_markup=ReplyKeyboardRemove(),
    )


async def cancel(update, context) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Bye! I hope we can talk again some day.", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def help(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')


async def set_timer(update, context) -> None:
    """Let the user specify a message to be sent back to him/her after the specified time."""
    chat_id = update.effective_message.chat_id
    try:
        # args[0] should contain the time for the timer in seconds
        # Then, should be the text message to be sent after time's over
        due = float(context.args[0])

        if due < 0:
            await update.effective_message.reply_text("Sorry we can not go back to future!")
            return

        temp = ""
        for i in range(1, len(context.args)):
            temp += context.args[i] + " "

        temp = temp if temp else "Hey! your time's over!!"

        context.job_queue.run_once(
            functools.partial(alarm, message=temp), due, chat_id=chat_id,
            name=str(chat_id), data=due
        )

        await update.effective_message.reply_text("Timer successfully set!")

    except (IndexError, ValueError):
        await update.effective_message.reply_text("Usage: /set <seconds>")


async def alarm(context, message) -> None:
    """Send the alarm message."""
    job = context.job
    await context.bot.send_message(job.chat_id, text=message)


def echo(update, context):
    """Echo the user message."""
    update.message.reply_text(update.message.text)


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # on different commands - answer in Telegram
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            GENDER: [MessageHandler(filters.Regex("^(Boy|Girl|Other)$"), gender)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("set", set_timer))
    application.add_handler(CommandHandler("help", help))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == '__main__':
    main()
