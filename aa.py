import telethon
from telethon import TelegramClient, events, functions, types
import asyncio
import re
import random
import time
from datetime import datetime, timedelta
import os
import json
import pytz
import sqlite3
import logging
from typing import List, Dict, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ACCOUNTS = [
    {"name": "session1", "app_id": 24966426, "api_hash": "78cc86a35e99aa707e6456179782641d"},
    {"name": "session2", "app_id": 27180402, "api_hash": "400c3285cd1eb6e8a638b45a90e7cba3"},
    {"name": "session3", "app_id": 29860564, "api_hash": "3e58281c574a1c9abfa8d50cbb55a6df"},
    {"name": "session4", "app_id": "29860564", "api_hash": "3e58281c574a1c9abfa8d50cbb55a6df"},
    {"name": "session5", "app_id": "15992426", "api_hash": "e32ed9721a2d3cddc3c080bd4c9e1346"}
]

OWNER_ID = 819127707

# Global variables
user_ids = {}
reply_tracking = {}
auto_posting_tasks = {}
auto_reply_settings = {
    'enabled': {},
    'message': {},
    'replied_users': {}
}
media_saving_settings = {}

def load_settings():
    global reply_tracking, auto_reply_settings, media_saving_settings
    try:
        if os.path.exists('settings.json'):
            with open('settings.json', 'r') as f:
                data = json.load(f)
                reply_tracking = data.get('reply_tracking', {})
                auto_reply_settings = data.get('auto_reply_settings', {
                    'enabled': {},
                    'message': {},
                    'replied_users': {}
                })
                media_saving_settings = data.get('media_saving_settings', {})
                
                # Convert keys to strings for consistency
                reply_tracking = {str(k): v for k, v in reply_tracking.items()}
                auto_reply_settings['enabled'] = {str(k): v for k, v in auto_reply_settings['enabled'].items()}
                auto_reply_settings['message'] = {str(k): v for k, v in auto_reply_settings['message'].items()}
                auto_reply_settings['replied_users'] = {str(k): set(v) for k, v in auto_reply_settings['replied_users'].items()}
                media_saving_settings = {str(k): v for k, v in media_saving_settings.items()}
    except Exception as e:
        print(f"Error loading settings: {e}")
        # Initialize default settings if loading fails
        reply_tracking = {}
        auto_reply_settings = {
            'enabled': {},
            'message': {},
            'replied_users': {}
        }
        media_saving_settings = {}

def save_settings():
    try:
        with open('settings.json', 'w') as f:
            json.dump({
                'reply_tracking': reply_tracking,
                'auto_reply_settings': {
                    'enabled': auto_reply_settings['enabled'],
                    'message': auto_reply_settings['message'],
                    'replied_users': {k: list(v) for k, v in auto_reply_settings['replied_users'].items()}
                },
                'media_saving_settings': media_saving_settings
            }, f, indent=4)
    except Exception as e:
        print(f"Error saving settings: {e}")

# Initialize clients with connection retries
clients = []
for acc in ACCOUNTS:
    client = TelegramClient(
        acc["name"],
        acc["app_id"],
        acc["api_hash"],
        connection_retries=5,
        request_retries=5,
        auto_reconnect=True
    )
    clients.append(client)

async def start_all_clients():
    for i, client in enumerate(clients, 1):
        try:
            await client.start()
            print(f"Account {i} started successfully")
        except Exception as e:
            print(f"Error starting account {i}: {e}")
            # Wait before retrying
            await asyncio.sleep(10)
            try:
                await client.start()
                print(f"Account {i} started successfully after retry")
            except Exception as e:
                print(f"Failed to start account {i} after retry: {e}")

async def get_user_ids():
    global user_ids
    for i, client in enumerate(clients, 1):
        try:
            me = await client.get_me()
            user_ids[i] = me.id
            print(f"User ID for account {i}: {me.id}")
        except Exception as e:
            print(f"Error getting user ID for account {i}: {e}")

def extract_entity_id(peer):
    if isinstance(peer, str):
        if peer.startswith('https://t.me/'):
            peer = peer.split('/')[-1]
        if peer.startswith('+') or peer.startswith('@'):
            return peer
        try:
            return int(peer)
        except ValueError:
            return peer
    return peer

def setup_handlers(client, account_num):
    @client.on(events.NewMessage(outgoing=True, pattern=r'^s (\d+) (\d+)$'))
    async def swing(event):
        try:
            if event.is_reply:
                geteventText = event.text.split(" ")
                sleps = int(geteventText[1])
                range_num = int(geteventText[2])
                chatId = event.chat_id
                message = await event.get_reply_message()
                
                auto_posting_tasks[account_num] = True
                
                for i in range(range_num):
                    if not auto_posting_tasks.get(account_num, True):
                        break
                    await asyncio.sleep(sleps)
                    try:
                        await client.send_message(chatId, message)
                    except Exception as e:
                        print(f"Error in auto-post: {str(e)}")
                        await asyncio.sleep(10)  # Wait longer on error
                
                if auto_posting_tasks.get(account_num, True):
                    await client.send_message("me", f"Auto-post completed in: {chatId} - Account {account_num}")
                else:
                    await client.send_message("me", f"Auto-post stopped manually in: {chatId} - Account {account_num}")
                
                auto_posting_tasks[account_num] = False
            else:
                await event.edit("Reply to a message to repeat it")
        except Exception as e:
            await event.edit(f"Error: {str(e)}")
            auto_posting_tasks[account_num] = False
    
    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.ن0$'))
    async def stop_auto_posting(event):
        try:
            if auto_posting_tasks.get(account_num, False):
                auto_posting_tasks[account_num] = False
                await event.edit("✅ تم إيقاف النشر التلقائي")
            else:
                await event.edit("⚠️ لا يوجد نشر تلقائي نشط لإيقافه")
        except Exception as e:
            await event.edit(f"Error: {str(e)}")
    
    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.ح([01])$'))
    async def toggle_reply_tracking(event):
        try:
            state = int(event.pattern_match.group(1))
            reply_tracking[str(account_num)] = bool(state)
            save_settings()
            status = "✅ تم تفعيل" if state else "❌ تم تعطيل"
            await event.edit(f"{status} تتبع الردود للحساب {account_num}")
        except Exception as e:
            await event.edit(f"Error: {str(e)}")
    
    @client.on(events.NewMessage(incoming=True))
    async def track_replies(event):
        try:
            if not reply_tracking.get(str(account_num), False):
                return
            
            if event.is_reply and event.sender_id != user_ids.get(account_num):
                replied_msg = await event.get_reply_message()
                
                if replied_msg and replied_msg.sender_id == user_ids.get(account_num):
                    chat = await event.get_chat()
                    chat_title = getattr(chat, 'title', "Private chat")
                    
                    sender = await event.get_sender()
                    sender_name = []
                    
                    if hasattr(sender, 'first_name') and sender.first_name:
                        sender_name.append(sender.first_name)
                    if hasattr(sender, 'last_name') and sender.last_name:
                        sender_name.append(sender.last_name)
                    
                    if not sender_name and hasattr(sender, 'username') and sender.username:
                        sender_name.append(f"@{sender.username}")
                    
                    if not sender_name:
                        sender_name.append(f"user_{sender.id}")
                    
                    sender_name = " ".join(sender_name).strip()
                    
                    message_text = event.text or "Non-text message (media)"
                    
                    chat_id = event.chat_id
                    if str(chat_id).startswith('-100'):
                        chat_id = int(str(chat_id)[4:])
                    
                    user_link = f"https://t.me/{sender.username}" if hasattr(sender, 'username') and sender.username else f"tg://user?id={sender.id}"
                    
                    message = (
                        f"📨 رد جديد على رسالتك\n\n"
                        f"👤 المرسل: {sender_name}\n"
                        f"🔗 حساب المرسل: {user_link}\n"
                        f"📝 المحتوى: {message_text}\n"
                        f"💬 المجموعة: {chat_title}\n"
                        f"🔗 رابط الرسالة: https://t.me/c/{chat_id}/{event.id}"
                    )
                    
                    await client.send_message("me", message)
        except Exception as e:
            print(f"Error tracking replies for account {account_num}: {str(e)}")

    # Auto-Reply Handlers
    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.ر1$'))
    async def enable_auto_reply(event):
        try:
            auto_reply_settings['enabled'][str(account_num)] = True
            save_settings()
            await event.edit(f"✅ تم تفعيل الرد التلقائي للحساب {account_num}")
        except Exception as e:
            await event.edit(f"Error: {str(e)}")

    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.ر0$'))
    async def disable_auto_reply(event):
        try:
            auto_reply_settings['enabled'][str(account_num)] = False
            save_settings()
            await event.edit(f"❌ تم تعطيل الرد التلقائي للحساب {account_num}")
        except Exception as e:
            await event.edit(f"Error: {str(e)}")

    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.ر2 (.+)$'))
    async def set_auto_reply_message(event):
        try:
            message = event.pattern_match.group(1).strip()
            auto_reply_settings['message'][str(account_num)] = message
            save_settings()
            await event.edit(f"📝 تم تعيين رسالة الرد التلقائي للحساب {account_num}:\n\n{message}")
        except Exception as e:
            await event.edit(f"Error: {str(e)}")

    # Media Saving Handlers
    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.و1$'))
    async def enable_media_saving(event):
        try:
            media_saving_settings[str(account_num)] = True
            save_settings()
            await event.edit(f"✅ تم تفعيل حفظ الوسائط الوقتية للحساب {account_num}")
        except Exception as e:
            await event.edit(f"Error: {str(e)}")

    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.و0$'))
    async def disable_media_saving(event):
        try:
            media_saving_settings[str(account_num)] = False
            save_settings()
            await event.edit(f"❌ تم تعطيل حفظ الوسائط الوقتية للحساب {account_num}")
        except Exception as e:
            await event.edit(f"Error: {str(e)}")

    @client.on(events.NewMessage(incoming=True))
    async def handle_auto_reply(event):
        try:
            account_str = str(account_num)
            
            if not auto_reply_settings['enabled'].get(account_str, False):
                return
            
            if not event.is_private:
                return
            
            sender = await event.get_sender()
            
            if sender.bot or sender.id == OWNER_ID:
                return
            
            if account_str not in auto_reply_settings['replied_users']:
                auto_reply_settings['replied_users'][account_str] = set()
            
            if sender.id not in auto_reply_settings['replied_users'][account_str]:
                reply_message = auto_reply_settings['message'].get(account_str, "شكراً على رسالتك!")
                await event.reply(reply_message)
                auto_reply_settings['replied_users'][account_str].add(sender.id)
                save_settings()
                
        except Exception as e:
            print(f"Error in auto-reply handler for account {account_num}: {str(e)}")

    @client.on(events.NewMessage(incoming=True))
    async def save_temporary_media(event):
        try:
            account_str = str(account_num)
            
            if not media_saving_settings.get(account_str, False):
                return
            
            if not event.is_private:
                return
            
            if event.media and hasattr(event.media, 'ttl_seconds'):
                media_path = await event.download_media()
                
                sender = await event.get_sender()
                sender_name = []
                
                first_name = getattr(sender, 'first_name', '')
                if first_name:
                    sender_name.append(first_name)
                
                last_name = getattr(sender, 'last_name', '')
                if last_name:
                    sender_name.append(last_name)
                
                if not sender_name:
                    username = getattr(sender, 'username', '')
                    if username:
                        sender_name.append(f"@{username}")
                    else:
                        sender_name.append(f"user_{sender.id}")
                
                sender_name = " ".join(sender_name).strip()
                
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                caption = (
                    f"🖼️ وسائط وقتية\n\n"
                    f"👤 المرسل: {sender_name}\n"
                    f"⏰ التاريخ: {now}\n"
                    f"🔗 المصدر: https://t.me/c/{event.chat_id}/{event.id}"
                )
                
                await client.send_file(
                    'me',
                    media_path,
                    caption=caption,
                    force_document=True
                )
                
                if os.path.exists(media_path):
                    os.remove(media_path)
                
        except Exception as e:
            print(f"Error saving temporary media for account {account_num}: {str(e)}")

    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.الاوامر$'))
    async def show_commands(event):
        try:
            commands = [
                "📜 قائمة الأوامر المتاحة:",
                "",
                "🔹 النشر التلقائي:",
                "- s [ثواني] [عدد] - نشر رسالة معينة تلقائياً (الرد على الرسالة)",
                "- .ن0 - إيقاف النشر التلقائي",
                "",
                "🔹 تتبع الردود:",
                "- .ح1 - تفعيل تتبع الردود",
                "- .ح0 - تعطيل تتبع الردود",
                "",
                "🔹 الرد التلقائي:",
                "- .ر1 - تفعيل الرد التلقائي",
                "- .ر0 - تعطيل الرد التلقائي",
                "- .ر2 [رسالة] - تعيين رسالة الرد التلقائي",
                "",
                "🔹 حفظ الوسائط الوقتية:",
                "- .و1 - تفعيل حفظ الوسائط الوقتية",
                "- .و0 - تعطيل حفظ الوسائط الوقتية",
                "",
                "🔹 أخرى:",
                "- .الاوامر - عرض هذه القائمة"
            ]
            
            await event.edit("\n".join(commands))
        except Exception as e:
            await event.edit(f"Error: {str(e)}")

async def main():
    print("Starting Telegram bot optimized for PythonAnywhere...")
    
    load_settings()
    
    # Initialize with retries
    max_retries = 3
    for attempt in range(max_retries):
        try:
            await start_all_clients()
            await get_user_ids()
            break
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt == max_retries - 1:
                print("Max retries reached, exiting...")
                return
            await asyncio.sleep(10)
    
    for i, client in enumerate(clients, 1):
        setup_handlers(client, i)
        auto_posting_tasks[i] = False
        if str(i) not in auto_reply_settings['replied_users']:
            auto_reply_settings['replied_users'][str(i)] = set()
        if str(i) not in media_saving_settings:
            media_saving_settings[str(i)] = False
    
    print("All systems operational!")
    print("Available commands:")
    print("- s [seconds] [count] - Auto-post message (reply to message)")
    print("- .ن0 - Stop auto-posting")
    print("- .ح1 - Enable reply tracking")
    print("- .ح0 - Disable reply tracking")
    print("- .ر1 - Enable auto reply")
    print("- .ر0 - Disable auto reply")
    print("- .ر2 [message] - Set auto reply message")
    print("- .و1 - Enable temporary media saving")
    print("- .و0 - Disable temporary media saving")
    print("- .الاوامر - Show all commands")
    
    # Keep the bot running with reconnection logic
    while True:
        try:
            await asyncio.gather(*[client.run_until_disconnected() for client in clients])
        except Exception as e:
            print(f"Connection error: {str(e)}")
            print("Reconnecting in 10 seconds...")
            await asyncio.sleep(10)
            try:
                await start_all_clients()
            except Exception as e:
                print(f"Reconnection failed: {str(e)}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped by user")
    except Exception as e:
        print(f"Fatal error: {str(e)}")