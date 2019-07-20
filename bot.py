#!/usr/bin/env python3
# Works with Python 3.7

import asyncio
import json
import logging

import aiohttp
from telegram import ParseMode
from telegram.ext import CommandHandler, Updater

with open("auth.json") as data_file:
    auth = json.load(data_file)
with open("links.json") as data_file:
    data = json.load(data_file)
with open("params.json") as data_file:
    params = json.load(data_file)

TOKEN = auth["token"]

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


async def fetch(session, url):
    try:
        async with session.get(url) as response:
            return await response.json(content_type=None)
    except Exception:
        return None


async def fetch_all(urls, loop):
    async with aiohttp.ClientSession(loop=loop, connector=aiohttp.TCPConnector(ssl=False)) as session:
        results = await asyncio.gather(*[fetch(session, url) for url in urls], return_exceptions=True)
        return results


def url_fetch(url_list):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(fetch_all(url_list, loop))


def help(update, context):
    message = "\n".join(data["help"])
    update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)


def links(update, context):
    message = "\n".join(data["links"])
    update.message.reply_text(message, parse_mode=ParseMode.HTML, disable_web_page_preview=True)


def roadmap(update, context):
    message = f"{data['roadmap']}"
    update.message.reply_text(message, parse_mode=ParseMode.HTML, disable_web_page_preview=True)


def por(update, context):
    message = f"{data['por']}"
    update.message.reply_text(message, parse_mode=ParseMode.HTML, disable_web_page_preview=True)


def about(update, context):
    message = "\n".join(data["about"])
    update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)


def calc(update, context):
    if len(context.args) < 1:
        message = f"{data['hpow']['default']}"
        update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
        return
    cmd = context.args[0].lower()
    if cmd == "infinity" or cmd == "infinite" or cmd == "inf":
        message = f"{data['hpow']['infinity']}"
    elif not is_number(cmd):
        message = f"{data['hpow']['default']}"
    elif cmd == "0":
        message = f"{data['hpow']['zero']}"
    elif is_number(cmd) and float(cmd) < 0:
        message = f"{data['hpow']['neg']}"
    elif is_number(cmd):
        url_list = [data["blocks_info"], data["rates"], data["net_hash"]]
        htmls = url_fetch(url_list)

        for i in range(len(htmls)):
            if htmls[i] is None:
                message = f"There was an error with {url_list[i]} api."
                update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
                return
        now = htmls[0]["blocks"][0]["time"]
        if len(htmls[0]["blocks"]) > 1:
            max_blocks = len(htmls[0]["blocks"]) - 1
            before = htmls[0]["blocks"][max_blocks]["time"]
            avg_bt = (now - before) / max_blocks
        else:
            avg_bt = 60

        for i in range(len(htmls[1])):
            if htmls[1][i]["code"] == "XSG":
                xsg_usd_price = float(htmls[1][i]["price"])

        hashrate = htmls[2]["info"]["networksolps"]
        mnr_rwd = float(params["mnr_rwd"])
        cmd = float(cmd)
        message = (
            f"Current network hashrate is *{int(hashrate)/1000:1.2f} KSols/s*.\nA hashrate of *{cmd:1.0f}"
            + f" Sols/s* will get you approximately *{cmd/hashrate*3600*mnr_rwd/avg_bt:1.2f} XSG* _("
            + f"{cmd/hashrate*3600*mnr_rwd/avg_bt*xsg_usd_price:1.2f}$)_ per *hour* and *"
            + f"{cmd/hashrate*3600*mnr_rwd*24/avg_bt:1.2f} XSG* _("
            + f"{cmd/hashrate*3600*mnr_rwd*24/avg_bt*xsg_usd_price:1.2f}$)_ per *day* at current "
            + "network difficulty."
        )
    update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)


def error(update, context):
    # Log Errors caused by Updates.
    logger.warning(f"Update {update} caused error {context.error}")


def main():
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(token=TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("help", help))
    dispatcher.add_handler(CommandHandler("links", links))
    dispatcher.add_handler(CommandHandler("roadmap", roadmap))
    dispatcher.add_handler(CommandHandler("por", por))
    dispatcher.add_handler(CommandHandler("about", about))
    dispatcher.add_handler(CommandHandler("calc", calc, pass_args=True))
    dispatcher.add_error_handler(error)

    # Start the bot
    updater.start_polling()

    # Run the bot until the user press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()


if __name__ == "__main__":
    main()
