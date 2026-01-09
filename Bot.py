import os
import re
import uuid
from pyrogram import Client, filters
from pyrogram.types import (
    InputStickerSetItem,
    InlineQueryResultArticle,
    InputTextMessageContent
)
from PIL import Image
from tinydb import TinyDB, Query
from config import *

# ---------------- CONFIG ---------------- #

os.makedirs("temp", exist_ok=True)
db = TinyDB("packs.json")
Pack = Query()

bot = Client(
    "AdvancedKangBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ---------------- UTILS ---------------- #

def get_emoji(text):
    if not text:
        return DEFAULT_EMOJI
    emojis = re.findall(r'[\U0001F300-\U0001FAFF]', text)
    return emojis[0] if emojis else DEFAULT_EMOJI

def resize_photo(path):
    img = Image.open(path).convert("RGBA")
    img.thumbnail((512, 512))
    img.save(path)

def get_pack_title(user, num):
    data = db.get(Pack.uid == user.id)
    if data and str(num) in data.get("packs", {}):
        return data["packs"][str(num)]
    return f"{user.first_name}'s Kang Pack Vol.{num}"

def get_pack(user, num):
    name = f"u{user.id}_kang_{num}_by_{bot.me.username}"
    title = get_pack_title(user, num)
    return name, title

# ---------------- KANG COMMAND ---------------- #

@bot.on_message(filters.command("kang") & filters.reply)
async def kang(_, msg):
    reply = msg.reply_to_message
    user = msg.from_user

    arg = msg.command[1] if len(msg.command) > 1 else "1"
    num = str(uuid.uuid4())[:5] if arg.lower() == "new" else arg

    pack_name, pack_title = get_pack(user, num)
    emoji = get_emoji(msg.text or reply.caption)

    file = await reply.download(file_name=f"temp/{uuid.uuid4()}")

    animated = reply.sticker and reply.sticker.is_animated
    video = reply.sticker and reply.sticker.is_video

    if not animated and not video:
        resize_photo(file)

    sticker = InputStickerSetItem(
        sticker=file,
        emoji_list=[emoji]
    )

    try:
        await bot.create_sticker_set(
            user_id=user.id,
            name=pack_name,
            title=pack_title,
            stickers=[sticker],
            animated=animated,
            videos=video
        )
        text = f"✅ **Sticker Pack Created!**\nhttps://t.me/addstickers/{pack_name}"
    except Exception:
        await bot.add_sticker_to_set(
            user_id=user.id,
            name=pack_name,
            sticker=sticker
        )
        text = "➕ Sticker added to existing pack!"

    await msg.reply(text)
    os.remove(file)

# ---------------- PACK NAME SYSTEM ---------------- #

@bot.on_message(filters.command("setpack"))
async def set_pack(_, msg):
    if len(msg.command) < 3:
        return await msg.reply("❌ Usage:\n`/setpack <pack_no> <pack name>`")

    num = msg.command[1]
    title = " ".join(msg.command[2:])
    uid = msg.from_user.id

    data = db.get(Pack.uid == uid)
    if not data:
        db.insert({"uid": uid, "packs": {num: title}})
    else:
        packs = data["packs"]
        packs[num] = title
        db.update({"packs": packs}, Pack.uid == uid)

    await msg.reply(f"✅ Pack **{num}** name set:\n**{title}**")

@bot.on_message(filters.command("getpack"))
async def get_pack_name(_, msg):
    if len(msg.command) < 2:
        return await msg.reply("❌ Usage:\n`/getpack <pack_no>`")

    num = msg.command[1]
    data = db.get(Pack.uid == msg.from_user.id)

    if not data or num not in data.get("packs", {}):
        return await msg.reply("⚠️ Is pack ka custom name set nahi hai.")

    await msg.reply(f"📦 Pack {num} name:\n**{data['packs'][num]}**")

@bot.on_message(filters.command("delpack"))
async def del_pack(_, msg):
    if len(msg.command) < 2:
        return await msg.reply("❌ Usage:\n`/delpack <pack_no>`")

    num = msg.command[1]
    uid = msg.from_user.id
    data = db.get(Pack.uid == uid)

    if not data or num not in data.get("packs", {}):
        return await msg.reply("⚠️ Pack name exist nahi karta.")

    packs = data["packs"]
    del packs[num]
    db.update({"packs": packs}, Pack.uid == uid)

    await msg.reply(f"🗑️ Pack {num} ka custom name hata diya.")

# ---------------- INLINE ---------------- #

@bot.on_inline_query()
async def inline_kang(_, q):
    await q.answer(
        [
            InlineQueryResultArticle(
                title="Kang Sticker",
                description="Reply sticker/photo/video + /kang",
                input_message_content=InputTextMessageContent(
                    "Reply kisi sticker/photo/video ko aur `/kang` likho 😎"
                )
            )
        ],
        cache_time=1
    )

# ---------------- START ---------------- #

@bot.on_message(filters.command("start"))
async def start(_, msg):
    await msg.reply(
        "**🔥 Advanced Kang Bot Ready!**\n\n"
        "Reply to sticker/photo/video:\n"
        "`/kang`\n"
        "`/kang 2`\n"
        "`/kang new`\n\n"
        "Pack name:\n"
        "`/setpack 1 My Stickers`\n"
        "`/getpack 1`\n"
        "`/delpack 1`\n\n"
        "Inline: `@BotUsername kang`"
    )

bot.run()

