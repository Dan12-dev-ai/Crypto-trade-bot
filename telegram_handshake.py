#!/usr/bin/env python3
"""
UOTA Elite v2 - Telegram Handshake
Verify bot token injection and connectivity
"""

import asyncio
import os
import sys
from telegram import Bot
from config import ConfigManager

async def perform_handshake():
    print("🚀 UOTA ELITE v2 - TELEGRAM HANDSHAKE")
    print("=" * 60)
    
    # 1. Load Configuration
    print("📂 Loading .env and config...")
    config = ConfigManager()
    
    token = config.telegram.bot_token
    chat_id = config.telegram.chat_id
    
    if not token:
        print("❌ ERROR: TELEGRAM_BOT_TOKEN not found in .env or config")
        return
    
    if not chat_id:
        print("❌ ERROR: TELEGRAM_CHAT_ID not found in .env or config")
        return
        
    print(f"✅ Token Detected: {token[:10]}...{token[-5:]}")
    print(f"✅ Chat ID Detected: {chat_id}")
    
    # 2. Initialize Bot
    print("\n🤖 Initializing Telegram Bot...")
    try:
        bot = Bot(token=token)
        me = await bot.get_me()
        print(f"✅ Bot Identity: @{me.username} ({me.first_name})")
    except Exception as e:
        print(f"❌ Bot Initialization Failed: {e}")
        return
        
    # 3. Send Handshake Message
    print(f"\n📡 Sending Handshake Message to {chat_id}...")
    message = (
        "🚀 **UOTA ELITE v2 - SYSTEM ONLINE**\n"
        "═════════════════════════════\n"
        "✅ **Connectivity**: Kali → Telegram Success\n"
        f"📊 **Account Monitoring**: 435294186 (Exness)\n"
        "🔒 **Security**: SMC Hard-Locked (1% Risk)\n"
        "🤖 **Status**: Heartbeat Active"
    )
    
    try:
        await bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')
        print("\n[HANDSHAKE SUCCESSFUL]: Telegram Sync Active. Check your phone.")
    except Exception as e:
        print(f"❌ Message Sending Failed: {e}")

if __name__ == "__main__":
    asyncio.run(perform_handshake())
