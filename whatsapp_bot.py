import logging
from pymongo import MongoClient
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from dotenv import load_dotenv
import os

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")


# Enable Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client["telegram_bot"]
users_collection = db["users"]

async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    username = update.message.from_user.username or "Unknown"
    
    users_collection.update_one(
        {"user_id": user_id},
        {"$setOnInsert": {"user_id": user_id, "username": username, "phone_numbers": []}},
        upsert=True
    )

    await update.message.reply_text("Send me a phone number, and I'll generate a WhatsApp link!")

async def handle_number(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    number = update.message.text.strip()

    if number.isdigit() and len(number) >= 10:
        whatsapp_link = f"https://wa.me/{number}"

        # Store number in MongoDB (Appending to history)
        users_collection.update_one(
            {"user_id": user_id},
            {"$push": {"phone_numbers": number}}
        )

        await update.message.reply_text(f"Click here to chat on WhatsApp: [Open WhatsApp]({whatsapp_link})", parse_mode="Markdown")
    else:
        await update.message.reply_text("Please send a valid phone number.")

# Command to Show User Data (For Admin)
async def user_data(update: Update, context: CallbackContext) -> None:
    users = users_collection.find({}, {"_id": 0, "username": 1, "phone_numbers": 1})

    msg = "\n".join([f"{user['username']}: {', '.join(user['phone_numbers'])}" for user in users])
    await update.message.reply_text(f"User Data:\n{msg}" if msg else "No users found!")

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("userdata", user_data))  # Show user history
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
