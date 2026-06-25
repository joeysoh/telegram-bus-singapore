import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.ext import MessageHandler, filters
from dotenv import load_dotenv
import llm
import re

def escape_markdown_v2(text: str) -> str:
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

loaded = load_dotenv()
API_KEY = os.getenv('TELEGRAM_BUS_BOT_TOKEN')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    for _ in range(2):
        reply = await llm.message(user_text)
        if len(reply.strip()) > 0:
            break        
    reply = escape_markdown_v2(f"{reply}")
    await update.message.reply_text(text=f"{reply}",parse_mode="MarkdownV2")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! Please provide 5 digit bus stop number and optionally a bus service number.")

if __name__ == "__main__":
    app = Application.builder().token(API_KEY).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot is polling locally...")
    app.run_polling()