import os
import asyncio
from pyrogram import Client as Bot, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ChatMemberUpdated
from pymongo import MongoClient


API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID"))
MONGO_URI = os.environ.get("MONGO_URI") 


mongo_client = MongoClient(MONGO_URI)
db = mongo_client["autoban_bot_db"]
groups_col = db["groups"]

bot = Bot(
    'left_ban_bot',
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)


@bot.on_message(filters.command('start') & filters.private)
async def start(bot, message: Message):
    bot_user = await bot.get_me()
    bot_username = bot_user.username
    
    text = (
        '👋 Hey, I am Autoban Bot \n\n'
        'I Can Ban a Member After Leaving The group. \n\n'
        '⚠️ Warning- My use is for personal Groups.'
    )
    
    reply_markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "➕ Add Me To Your Group ➕", 
                    url=f"https://t.me/{bot_username}?startgroup=true"
                )
            ]
        ]
    )
    
    await message.reply(text, reply_markup=reply_markup, quote=True)


# 
@bot.on_chat_member_updated()
async def ban_left_member(bot, event: ChatMemberUpdated):
    try:
        # 
        if event.old_chat_member and not event.new_chat_member:
            #
            left_user = event.old_chat_member.user
            chat_id = event.chat.id
            
            #
            if left_user.id != bot.me.id:
                await bot.ban_chat_member(chat_id, left_user.id)
                print(f"✅ Banned Left User: {left_user.id} (Username: @{left_user.username}) in Chat: {chat_id}")
                
    except Exception as e:
        print(f"❌ Error banning user: {e}")


@bot.on_message(filters.group, group=-1)
async def track_groups(bot, m: Message):
    
    if not groups_col.find_one({"chat_id": m.chat.id}):
        groups_col.insert_one({"chat_id": m.chat.id})
        print(f"📝 New Group Added to Database: {m.chat.id}")



@bot.on_message(filters.command('broadcast') & filters.user(OWNER_ID))
async def broadcast(bot, message: Message):
    if not message.reply_to_message and len(message.command) < 2:
        await message.reply("သုံးစွဲပုံ - /broadcast ပို့ချင်သောစာ သို့မဟုတ် စာတစ်စောင်ကို reply ပြန်ပြီး /broadcast ဟု ရိုက်ပါ။")
        return

    msg_to_send = message.reply_to_message if message.reply_to_message else message
    text_mode = False if message.reply_to_message else True

    status_msg = await message.reply("📢 Broadcast စတင်ပို့ဆောင်နေပါပြီ...")
    success = 0
    failed = 0

    all_groups = groups_col.find()

    for group in all_groups:
        chat_id = group["chat_id"]
        try:
            if text_mode:
                broadcast_text = message.text.split(None, 1)[1]
                await bot.send_message(chat_id, broadcast_text)
            else:
                await msg_to_send.copy(chat_id)
            success += 1
            await asyncio.sleep(0.3)
        except Exception as e:
            failed += 1
            groups_col.delete_one({"chat_id": chat_id})
            print(f"❌ Failed to send to {chat_id} (Removed from DB): {e}")

    await status_msg.edit(f"📢 Broadcast ပို့ဆောင်ပြီးစီးပါပြီ!\n\n✅ အောင်မြင် - {success} ခု\n❌ ကျရှုံး - {failed} ခု")


bot.run()
