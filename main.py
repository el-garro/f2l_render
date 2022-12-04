# fmt: off
from logging import basicConfig, log, INFO, WARN, ERROR, CRITICAL
from pathlib import Path
from random import randbytes
from requests import get

basicConfig(format="[%(levelname)s]: %(message)s", level=INFO, force=True)
log(INFO, "Initializing...")
# fmt: on

from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from pyrogram.enums.parse_mode import ParseMode
from os import system, unlink
from threading import Thread
from inspect import iscoroutinefunction
from time import sleep, time
import bot_cfg

bot: Client = Client(
    "bot",
    api_id=bot_cfg.tg_api_id,
    api_hash=bot_cfg.tg_api_hash,
    bot_token=bot_cfg.tg_bot_token,
)
bot.set_parse_mode(ParseMode.DISABLED)


def slow(interval: int):
    def dec(func):
        last_update = [
            time()
        ]  # It needs to be mutable from the wrapper, hence the list

        # Sync wrapper
        def wrap_sync(*args, **kwargs):
            now = time()
            if now - last_update[0] < interval:
                return
            last_update[0] = now
            return func(*args, **kwargs)

        # Async wrapper
        async def wrap_async(*args, **kwargs):
            now = time()
            if now - last_update[0] < interval:
                return
            last_update[0] = now
            return await func(*args, **kwargs)

        if iscoroutinefunction(func):
            return wrap_async
        else:
            return wrap_sync

    return dec


@slow(2)
async def progress_bar(current: int, total: int, progress_msg: Message):
    try:
        await progress_msg.edit_text(f"⏳ Descargando... {(100 * current // total)}%")
    except:
        pass


@bot.on_message(filters.command("start") & filters.private)
async def welcome(client: Client, message: Message):
    await message.reply("Bienvenido")


@bot.on_message(filters.media & filters.private)
async def download_media(client: Client, message: Message):
    if not (message.from_user.username in bot_cfg.bot_users):
        log(WARN, f"UNAUTHORIZED: {message.from_user.username}({message.from_user.id})")
        return

    log(INFO, f"Downloading: {message.media.name}")
    progress_msg: Message = await message.reply("⏳ Descargando... 0%", quote=True)
    try:
        fpath = await message.download(
            file_name=f"./downloads/{randbytes(1).hex()}/",
            progress=progress_bar,
            progress_args=(progress_msg,),
        )
    except:
        log(ERROR, f"Error downloading: {message.media.name}")
        try:
            await progress_msg.edit("❌ Error durante la descarga.")
        except:
            pass
        return

    fpath = Path(fpath)
    url = f"https://{bot_cfg.render_url}/{fpath.parent.name}/{fpath.name}"
    log(INFO, f"Downloaded: {url}")
    try:
        buttons = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Eliminar", "delete")]])
        await progress_msg.edit(
            url, reply_markup=buttons, disable_web_page_preview=True
        )
    except:
        pass


@bot.on_callback_query(filters.regex(r"^delete$"))
async def delete(client: Client, query: CallbackQuery):
    url = Path(query.message.text)
    fpath = f"./downloads/{url.parent.name}/{url.name}"
    log(INFO, f"Delete: {fpath}")
    await query.answer("Eliminando...")
    try:
        unlink(fpath)
        await query.message.delete()
    except:
        pass


def webserver():
    log(INFO, f"Starting webserver on {bot_cfg.render_web_port}")
    system(f"python -m http.server -d ./downloads/ {bot_cfg.render_web_port}")
    # run(["python", "-m", "http.server", "-d", "./downloads/", bot_cfg.fly_web_port])


def heartbeat():
    while True:
        try:
            get(f"https://{bot_cfg.render_url}/")
            log(INFO, "Heartbeat")
        except:
            pass

        sleep(10 * 60)


log(INFO, "Starting...")
Thread(target=webserver).start()
Thread(target=heartbeat).start()
bot.run()
