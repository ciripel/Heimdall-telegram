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


def net_stats(update, context):
    url_list = [data["blocks_info"], data["net_status"]]
    htmls = url_fetch(url_list)
    for i in range(len(htmls)):
        if htmls[i] is None:
            message = f"There was an error with {url_list[i]} api."
            update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            logger.warning(f"There was an error with {url_list[i]} api.")
            return

    now = htmls[0]["blocks"][0]["time"]
    if len(htmls[0]["blocks"]) > 1:
        max_blocks = len(htmls[0]["blocks"]) - 1
        before = htmls[0]["blocks"][max_blocks]["time"]
        avg_bt = (now - before) / max_blocks
    else:
        avg_bt = 60
    last_block = htmls[0]["blocks"][0]["height"]
    version = params["daemon_ver"]
    diff = htmls[1]["info"]["difficulty"]
    hashrate = htmls[1]["info"]["networksolps"]

    message = (
        f"• Version • *{version}*\n• Block Height • *{last_block:,}*\n• Avg Block Time • *{round(avg_bt, 2)}"
        + f" s*\n• Network Hashrate • *{int(hashrate)/1000} kSol/s*\n• Network Difficulty • *{diff:1.3f}*"
    )
    update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)


def halving(update, context):
    url_list = [data["blocks_info"]]
    htmls = url_fetch(url_list)
    if htmls[0] is None:
        message = f"There was an error with {url_list[0]} api."
        update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
        logger.warning(f"There was an error with {url_list[0]} api.")
        return

    now = htmls[0]["blocks"][0]["time"]
    if len(htmls[0]["blocks"]) > 1:
        max_blocks = len(htmls[0]["blocks"]) - 1
        before = htmls[0]["blocks"][max_blocks]["time"]
        avg_bt = (now - before) / max_blocks
    else:
        avg_bt = 60
    last_block = htmls[0]["blocks"][0]["height"]
    halving_time = (2102400 - last_block) * avg_bt / 86400
    message = (
        f"The next halving will be in approximately *{halving_time:1.2f}* days (*{halving_time/365:1.3f}"
        + "* years).\nThe block reward after the halving will be *10* XSG."
    )
    update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)


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
        url_list = [data["blocks_info"], data["rates"], data["net_status"]]
        htmls = url_fetch(url_list)
        for i in range(len(htmls)):
            if htmls[i] is None:
                message = f"There was an error with {url_list[i]} api."
                update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
                logger.warning(f"There was an error with {url_list[i]} api.")
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


def mninfo(update, context):
    url_list = [data["blocks_info"], data["masternodes"]["link"], data["masternodes"]["asgard_managed"]]
    htmls = url_fetch(url_list)
    for i in range(len(htmls) - 1):
        if htmls[i] is None:
            message = f"There was an error with {url_list[i]} api."
            update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            logger.warning(f"There was an error with {url_list[i]} api.")
            return
    if htmls[2] is None:
        htmls[2] = 0
        logger.warning(f"There was an error with {data['masternodes']['asgard_managed']} api.")

    now = htmls[0]["blocks"][0]["time"]
    if len(htmls[0]["blocks"]) > 1:
        max_blocks = len(htmls[0]["blocks"]) - 1
        before = htmls[0]["blocks"][max_blocks]["time"]
        avg_bt = (now - before) / max_blocks
    else:
        avg_bt = 60
    mn_count_s = json.dumps(htmls[1])
    mn_count = mn_count_s.count("ENABLED")
    asgard_managed = htmls[2]
    mn_rwd = float(params["mn_rwd"])
    guide_link = data["masternodes"]["guide_link"]
    asgard = data["masternodes"]["asgard"]
    asgard_vid = data["masternodes"]["asgard_vid"]
    mn_roi = mn_rwd * 3153600 / avg_bt / mn_count / 10
    time_first_payment = 2.6 * mn_count / 60
    message = (
        f"• Active masternodes • <b>{mn_count: 1.0f}</b> (<b>{asgard_managed}</b><i> managed by </i><b>Asgard</b>)"
        + f"\n• Coins Locked • <b>{mn_count*10000:,} XSG</b>\n• ROI "
        + f"• <b>{mn_roi: 1.3f} % </b>\n• Minimum time before first payment • <b>{time_first_payment: 1.2f} hours</b>"
        + f"\n• One masternode will give you approximately <b>{3600*24/avg_bt*mn_rwd/mn_count:1.3f} XSG</b> per"
        + f" <b>day</b>\n{asgard}{asgard_vid}{guide_link}"
    )
    update.message.reply_text(message, parse_mode=ParseMode.HTML, disable_web_page_preview=True)


def mnrew(update, context):
    url_list = [data["blocks_info"], data["rates"], data["masternodes"]["link"]]
    htmls = url_fetch(url_list)
    for i in range(len(htmls)):
        if htmls[i] is None:
            message = f"There was an error with {url_list[i]} api."
            update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            logger.warning(f"There was an error with {url_list[i]} api.")
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
    mn_count_s = json.dumps(htmls[2])
    mn_count = mn_count_s.count("ENABLED")
    mn_rwd = float(params["mn_rwd"])
    if len(context.args) < 1:
        message = (
            f"*1* Masternode will give you approximately:"
            + f"\n*{3600*24/avg_bt*mn_rwd/mn_count:1.3f} XSG* _("
            + f"{3600*24/avg_bt*mn_rwd/mn_count*xsg_usd_price:1.3f}$)_ per *day*"
            + f"\n*{3600*24*7/avg_bt*mn_rwd/mn_count:1.3f} XSG* _("
            + f"{3600*24*7/avg_bt*mn_rwd/mn_count*xsg_usd_price:1.3f}$)_ per *week*"
            + f"\n*{3600*24*30/avg_bt*mn_rwd/mn_count:1.3f} XSG* _("
            + f"{3600*24*30/avg_bt*mn_rwd/mn_count*xsg_usd_price:1.3f}$)_ per *month*"
            + f"\n*{3600*24*365/avg_bt*mn_rwd/mn_count:1.3f} XSG* _("
            + f"{3600*24*365/avg_bt*mn_rwd/mn_count*xsg_usd_price:1.3f}$)_ per *year*"
        )
        update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
        return
    cmd = context.args[0].lower()
    if not is_number(cmd):
        message = f"{data['mnrewards']['default']}"
    elif cmd == "0":
        message = f"{data['mnrewards']['zero']}"
    elif is_number(cmd) and float(cmd) < 0:
        message = f"{data['mnrewards']['neg']}"
    elif is_number(cmd):
        cmd = float(cmd)
        message = (
            f"*{cmd:1.0f}* Masternode will give you approximately:"
            + f"\n*{cmd*3600*24/avg_bt*mn_rwd/mn_count:1.3f} XSG* _("
            + f"{cmd*3600*24/avg_bt*mn_rwd/mn_count*xsg_usd_price:1.3f}$)_ per *day*"
            + f"\n*{cmd*3600*24*7/avg_bt*mn_rwd/mn_count:1.3f} XSG* _("
            + f"{cmd*3600*24*7/avg_bt*mn_rwd/mn_count*xsg_usd_price:1.3f}$)_ per *week*"
            + f"\n*{cmd*3600*24*30/avg_bt*mn_rwd/mn_count:1.3f} XSG* _("
            + f"{cmd*3600*24*30/avg_bt*mn_rwd/mn_count*xsg_usd_price:1.3f}$)_ per *month*"
            + f"\n*{cmd*3600*24*365/avg_bt*mn_rwd/mn_count:1.3f} XSG* _("
            + f"{cmd*3600*24*365/avg_bt*mn_rwd/mn_count*xsg_usd_price:1.3f}$)_ per *year*"
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
    dispatcher.add_handler(CommandHandler("net", net_stats))
    dispatcher.add_handler(CommandHandler("halving", halving))
    dispatcher.add_handler(CommandHandler("calc", calc, pass_args=True))
    dispatcher.add_handler(CommandHandler("mn", mninfo))
    dispatcher.add_handler(CommandHandler("mnrew", mnrew, pass_args=True))
    dispatcher.add_error_handler(error)

    # Start the bot
    updater.start_polling()

    # Run the bot until the user press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()


if __name__ == "__main__":
    main()
