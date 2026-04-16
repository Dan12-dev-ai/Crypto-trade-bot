#!/usr/bin/env python3
"""
Connect to DEDAN Agent Bot - UOTA Elite v2
"""

# import os  # Moved to function to avoid circular import
# import asyncio  # Moved to function to avoid circular import
from dotenv import load_dotenv
from telegram import Bot

async def connect_dedan_bot():
    """Connect to DEDAN Agent bot"""
    
    # Your bot token
    bot_token = "7994634538:AAHgzPGQqtcFqXHp4WZ9faL9NYMGfXZhBCk"
    
    print("🤖 Connecting to DEDAN Agent Bot...")
    print(f"🔑 Bot Token: {bot_token[:15]}...{bot_token[-10:]}")
    print()
    
    try:
        # Initialize bot
        bot = Bot(token=bot_token)
        
        # Get bot info
        bot_info = await bot.get_me()
        
        print(f"""
✅ BOT CONNECTED SUCCESSFULLY!

🤖 Bot Information:
- Name: {bot_info.first_name}
- Username: @{bot_info.username}
- ID: {bot_info.id}
- Can receive messages: ✅

📱 NEXT STEPS:
1. Open Telegram
2. Search for: @{bot_info.username}
3. Send /start to your bot
4. I'll get your Chat ID automatically
        """)
        
        print("⏳ Waiting for you to send /start to your bot...")
        print("   (Press Enter once you've sent the message)")
        input()
        
        # Get updates to find Chat ID
        updates = await bot.get_updates()
        
        if not updates:
            print("❌ No messages found. Please send /start to your bot first.")
            return
        
        # Get the latest message
        latest_update = updates[-1]
        chat_id = latest_update.message.chat.id
        user_info = latest_update.message.from_user
        
        print(f"""
✅ CHAT ID FOUND!

👤 User Information:
- Name: {user_info.first_name} {user_info.last_name if user_info.last_name else ''}
- Username: @{user_info.username if user_info.username else 'N/A'}
- Chat ID: {chat_id}

🔧 UPDATING YOUR .env FILE...
        """)
        
        # Update .env file
        env_file = '.env'
        
        # Read current .env
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                env_content = f.read()
        else:
            env_content = ""
        
        # Update bot token and chat ID
        lines = env_content.split('\n')
        updated_lines = []
        
        token_updated = False
        chat_id_updated = False
        
        for line in lines:
            if line.startswith('TELEGRAM_BOT_TOKEN='):
                updated_lines.append(f'TELEGRAM_BOT_TOKEN={bot_token}')
                token_updated = True
            elif line.startswith('TELEGRAM_CHAT_ID='):
                updated_lines.append(f'TELEGRAM_CHAT_ID={chat_id}')
                chat_id_updated = True
            else:
                updated_lines.append(line)
        
        # Add missing entries
        if not token_updated:
            updated_lines.append(f'TELEGRAM_BOT_TOKEN={bot_token}')
        if not chat_id_updated:
            updated_lines.append(f'TELEGRAM_CHAT_ID={chat_id}')
        
        # Write updated .env
        with open(env_file, 'w') as f:
            f.write('\n'.join(updated_lines))
        
        print(f"""
✅ CONFIGURATION COMPLETE!

📋 Your .env file has been updated with:
TELEGRAM_BOT_TOKEN={bot_token}
TELEGRAM_CHAT_ID={chat_id}

🚀 READY TO START!
Now you can:
1. Start your agent: python3 master_controller.py
2. Control from Telegram with commands like:
   /status - Check system status
   /target 4000 - Set target
   /stop - Emergency stop
   /help - All commands

🎯 DEDAN Agent is ready for 24/7 operation!
        """)
        
        # Test sending a message
        print("\n📱 Sending test message to your bot...")
        await bot.send_message(
            chat_id=chat_id,
            text="""
🚀 **DEDAN Agent Connected!**

🤖 Bot: @dedan_agent_bot
👤 User: {user_info.first_name}
📱 Chat ID: {chat_id}
⏰ Time: {asyncio.get_event_loop().time()}

✅ Your agent is now connected and ready for commands!

🎯 Available Commands:
/status - Account balance and health
/target [amount] - Set monthly target
/report - XAUUSD chart with Order Blocks
/stop - Emergency stop all trading
/help - All commands

🛡️ Security: Only your Chat ID can control this bot
🔄 Immortal: 24/7 operation with auto-restart
🔒 Encrypted: AES-256 security protection
            """.format(
                user_info=user_info,
                chat_id=chat_id
            )
        )
        
        print("✅ Test message sent successfully!")
        print("📱 Check your Telegram - you should see the connection message!")
        
    except Exception as e:
        print(f"❌ Error connecting to bot: {e}")
        print("💡 Please check:")
        print("   1. Bot token is correct")
        print("   2. You sent /start to your bot")
        print("   3. Internet connection is working")

if __name__ == "__main__":
    asyncio.run(connect_dedan_bot())
