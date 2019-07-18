#!/usr/bin/env python3
# Works with Python 3.7

import json
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import CallbackQueryHandler, CommandHandler, Updater

with open("auth.json") as data_file:
    auth = json.load(data_file)
with open("links.json") as data_file:
    data = json.load(data_file)

TOKEN = auth["token"]

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


def start(update, context):
    keyboard = [
        [InlineKeyboardButton("Option 1", callback_data="1"),
         InlineKeyboardButton("Option 2", callback_data="2")],
        [InlineKeyboardButton("Option 3", callback_data="3")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Please choose:", reply_markup=reply_markup)


def button(update, context):
    query = update.callback_query
    query.edit_message_text(text=f"Selected option: {query.data}")


def help(update, context):
    message = "\n".join(data["commands"])
    update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)


def error(update, context):
    # Log Errors caused by Updates.
    logger.warning(f"Update {update} caused error {context.error}")


def main():
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(token=TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(button))
    dispatcher.add_handler(CommandHandler("help", help))
    dispatcher.add_error_handler(error)

    # Start the bot
    updater.start_polling()

    # Run the bot until the user press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()


if __name__ == "__main__":
    main()
