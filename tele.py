import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.ext import MessageHandler, filters
from dotenv import load_dotenv
import llm
import re

loaded = load_dotenv()
API_KEY = os.getenv('TELEGRAM_BUS_BOT_TOKEN')


# Matches MarkdownV2 entities so we can skip escaping inside them
ENTITY_PATTERN = re.compile(
    r'''
    (?P<pre>```.*?```)              # pre-formatted code block (multi-line)
    |(?P<code>`[^`\n]+`)            # inline code
    |(?P<bold>\*[^*\n]+\*)          # *bold*
    |(?P<underline>__[^_\n]+__)     # __underline__
    |(?P<italic>_[^_\n]+_)          # _italic_
    |(?P<strike>~[^~\n]+~)          # ~strikethrough~
    |(?P<spoiler>\|\|[^|\n]+\|\|)   # ||spoiler||
    |(?P<link>\[[^\]\n]+\]\([^)\n]+\))  # [text](url)
    ''',
    re.VERBOSE | re.DOTALL
)

ESCAPE_CHARS = r'_*[]()~`>#+-=|{}.!\\'

def _escape_literal(text: str) -> str:
    """Escape MarkdownV2 reserved chars in plain text (no markdown inside)."""
    return re.sub(f'([{re.escape(ESCAPE_CHARS)}])', r'\\\1', text)

def escape_markdown_v2(text: str) -> str:
    """
    Escape a string for MarkdownV2, but skip escaping inside recognized
    markdown entities (bold, italic, underline, strikethrough, code, links).
    Plain text outside those entities gets fully escaped.
    """
    result = []
    last_end = 0

    for match in ENTITY_PATTERN.finditer(text):
        start, end = match.span()
        # Escape the literal text before this entity
        result.append(_escape_literal(text[last_end:start]))
        # Leave the matched entity untouched
        result.append(match.group())
        last_end = end

    # Escape any trailing literal text after the last entity
    result.append(_escape_literal(text[last_end:]))

    return ''.join(result)

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