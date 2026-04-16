#!/usr/bin/env python3
"""
Get Telegram Chat ID - UOTA Elite v2
"""

# import os  # Moved to function to avoid circular import
# import asyncio  # Moved to function to avoid circular import
from dotenv import load_dotenv
from telegram import Bot

async def get_chat_id():
    """Get your Telegram Chat ID"""
    
    # Load environment
    load_dotenv()
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not bot_token:
        print("❌ Please set TELEGRAM_BOT_TOKEN in .env file first")
        return
    
    print("📱 Getting your Chat ID...")
    print("1. Send any message to your bot on Telegram")
    print("2. Press Enter to continue...")
    input()
    
    try:
        # Initialize bot
        bot = Bot(token=bot_token)
        
        # Get updates
        updates = await bot.get_updates()
        
        if not updates:
            print("❌ No messages found. Please send a message to your bot first.")
            return
        
        # Get the latest message
        latest_update = updates[-1]
        chat_id = latest_update.message.chat.id
        user_info = latest_update.message.from_user
        
        print(f"""
✅ SUCCESS! Your Chat ID is: {chat_id}

📋 COPY THIS TO YOUR .env FILE:
TELEGRAM_CHAT_ID={chat_id}

👤 User Info:
- Name: {user_info.first_name} {user_info.last_name if user_info.last_name else ''}
- Username: @{user_info.username if user_info.username else 'N/A'}
- Chat ID: {chat_id}

🚀 Now you can control your agent from Telegram!
        """)
        
        # Save to .env automatically
        with open('.env', 'r') as f:
            env_content = f.read()
        
        # Update or add TELEGRAM_CHAT_ID
        if 'TELEGRAM_CHAT_ID=' in env_content:
            # Replace existing
            lines = env_content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('TELEGRAM_CHAT_ID='):
                    lines[i] = f'TELEGRAM_CHAT_ID={chat_id}'
                    break
            env_content = '\n'.join(lines)
        else:
            # Add new line
            env_content += f'\nTELEGRAM_CHAT_ID={chat_id}'
        
        with open('.env', 'w') as f:
            f.write(env_content)
        
        print("✅ Chat ID automatically saved to .env file!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Make sure your bot token is correct and you sent a message to your bot")

if __name__ == "__main__":
    asyncio.run(get_chat_id())
