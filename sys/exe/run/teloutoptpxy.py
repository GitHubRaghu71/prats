import telegram
from cnstpxy import CNFG

async def send_telegram_message(message_text):
    try:
        # Define the bot token and your Telegram username or ID
        dct = CNFG["telegram"]
        bot_token = dct["bot_token"]  
        user_usernames = dct["chat_id"]  

        # Create a Telegram bot
        bot = telegram.Bot(token=bot_token)

        # Send the message to Telegram
        await bot.send_message(chat_id=user_usernames, text=message_text)

    except Exception as e:
        # Handle the exception (e.g., log it) and continue with your code
        print(f"Error sending message to Telegram: {e}")
