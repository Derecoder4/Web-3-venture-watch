# telegram_bot.py (V1.1 - Crypto Startup Pulse - Correct Keyboard)
import os
import requests
import feedparser # For parsing RSS feeds
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup # Keep ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext
from bs4 import BeautifulSoup # Keep for cleaning summaries if needed

# Load the secret keys from the .env file FIRST
load_dotenv()

# --- Import Custom Modules ---
from dobby_client import get_dobby_response # Uses default max_tokens=1024, temp=0.6

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# --- Define Main Keyboard (CORRECTED) ---
MAIN_KEYBOARD = [
    ["/latest", "/funding"],
    ["/defi", "/web3gaming"],
    ["/help", "/about"],
]
MAIN_MARKUP = ReplyKeyboardMarkup(MAIN_KEYBOARD, resize_keyboard=True)
# --- END CORRECTION ---

# (Tone and Quantity keyboards are not needed for this bot)

# --- RSS Feed Configuration ---
# Using TechCrunch for funding news - it will need AI filtering.
FEED_URLS = {
    "general": [
        "https://cointelegraph.com/rss/tag/startups",
        "https://decrypt.co/feed",
        "https://blockworks.co/feed",
        "https://www.coindesk.com/arc/outboundfeeds/rss/",
    ],
    "funding": [
        "https://techcrunch.com/feed/", # Added TechCrunch general feed
    ],
    "defi": [
        "https://cointelegraph.com/rss/tag/defi",
        "https://thedefiant.io/feed",
    ],
    "web3gaming": [
        "https://cointelegraph.com/rss/tag/gaming",
        "https://decrypt.co/feed/gaming",
    ]
}

# --- Profanity Filter ---
FORBIDDEN_WORDS = {
    "fuck": "f***", "fucking": "f***", "shit": "s***", "ass": "a**",
    "asshole": "a**hole", "damn": "darn", "bitch": "b****",
}

def filter_profanity(text: str) -> str:
    """Replaces common profanities in the text."""
    if not isinstance(text, str): return str(text) if text is not None else ""
    words = text.split(); cleaned_words = []
    for word in words:
        clean_word = word.strip('.,!?;:\'"').lower()
        replacement = FORBIDDEN_WORDS.get(clean_word)
        cleaned_words.append(word.lower().replace(clean_word, replacement) if replacement else word)
    return " ".join(cleaned_words)

# --- Utility Function for Sending Messages (Simple Split) ---
async def send_message(update: Update, context: CallbackContext, text: str, reply_markup=None):
    """Sends a message, splitting it simply by character limit if needed."""
    MAX_MESSAGE_LENGTH = 4096
    if not text:
        print("Warning: Attempted to send empty message.")
        await update.message.reply_text("Sorry, I couldn't generate a response.", reply_markup=reply_markup)
        return
    # Default to main keyboard if none provided explicitly
    final_markup = reply_markup if reply_markup is not None else MAIN_MARKUP

    if len(text) <= MAX_MESSAGE_LENGTH:
        try:
            await update.message.reply_text(text, reply_markup=final_markup)
        except Exception as e:
            print(f"Error sending single message part: {e}")
            await update.message.reply_text("Error: Could not send the response.", reply_markup=final_markup)
    else:
        parts = [text[i : i + MAX_MESSAGE_LENGTH] for i in range(0, len(text), MAX_MESSAGE_LENGTH)]
        for i, part in enumerate(parts):
            current_markup = final_markup if i == len(parts) - 1 else None
            try:
                await update.message.reply_text(part, reply_markup=current_markup)
            except Exception as e:
                print(f"Error sending message part {i+1}: {e}")
                if i == len(parts) - 1:
                     await update.message.reply_text("Error sending part of the message.", reply_markup=final_markup)

# --- RSS Fetching and Processing ---
def fetch_and_combine_feeds(category: str, num_articles: int = 5) -> str:
    """Fetches articles from RSS feeds for a category and combines relevant text."""
    combined_text = ""; urls_to_fetch = FEED_URLS.get(category, [])
    if not urls_to_fetch: return "Error: No RSS feeds configured for this category."
    print(f"Fetching feeds for category: {category}"); articles_found = 0
    for url in urls_to_fetch:
        try:
            feed = feedparser.parse(url)
            entries = feed.entries[:num_articles]
            for entry in entries:
                articles_found += 1
                title = entry.get('title', 'No Title')
                summary = entry.get('summary', entry.get('description', ''))
                summary_text = requests.utils.unquote(summary)
                if '<' in summary_text:
                     soup = BeautifulSoup(summary_text, 'html.parser')
                     summary_text = soup.get_text(separator=' ', strip=True)
                combined_text += f"Title: {title}\nSummary: {summary_text}\n---\n"
                if len(combined_text) > 4000: break
            if len(combined_text) > 4000: break
        except Exception as e: print(f"Error fetching/parsing feed {url}: {e}"); continue
    if articles_found == 0: return "No recent articles found in the feeds for this category."
    elif not combined_text: return "Found articles, but could not extract summaries."
    else: return combined_text[:4000]

# --- Command Handlers ---

async def start(update: Update, context: CallbackContext) -> None:
    welcome_text = (
        "Hi! I'm the Crypto Startup Pulse Bot, powered by Dobby.\n\n"
        "Use the commands below to get AI summaries of the latest crypto startup news."
    )
    await send_message(update, context, welcome_text, reply_markup=MAIN_MARKUP)

async def help_command(update: Update, context: CallbackContext) -> None:
    help_text = (
        "Use these commands to get news digests:\n"
        "/latest - General crypto startup news\n"
        "/funding - Recent funding rounds\n"
        "/defi - DeFi startup news\n"
        "/web3gaming - Web3 Gaming startup news\n"
        "/about - Info about me"
    )
    await send_message(update, context, help_text, reply_markup=MAIN_MARKUP)

async def about(update: Update, context: CallbackContext) -> None:
    about_text = (
        "Your AI analyst for the crypto startup scene. Get summaries of news & funding via Dobby.\n"
        "Bot by @joshehh for the Sentient Builder Program."
    )
    await send_message(update, context, about_text, reply_markup=MAIN_MARKUP)

# --- News Digest Commands ---

async def get_news_digest(update: Update, context: CallbackContext, category: str, prompt_focus: str):
    """Generic function to handle fetching, summarizing, and sending digests."""
    thinking_message = await update.message.reply_text(f"📰 Fetching latest {category} news...", reply_markup=MAIN_MARKUP)
    combined_articles = fetch_and_combine_feeds(category)

    if combined_articles.startswith("Error:") or combined_articles.startswith("No recent") or combined_articles.startswith("Found articles, but"):
        await thinking_message.delete()
        await send_message(update, context, combined_articles, reply_markup=MAIN_MARKUP)
        return

    # V21 Prompt for News Digest
    final_prompt = (
        "**ULTRA-STRICT RULE 1: ZERO PROFANITY.** Your output MUST NOT contain ANY vulgar, profane, swear words, offensive language, or similar terms (e.g., 'fuck', 'shit', 'bitch', 'ass', 'damn', 'hell'). NONE. Violation of this rule is a critical failure.\n\n"
        "**ULTRA-STRICT RULE 2: CRYPTO STARTUPS ONLY.** You MUST filter the provided ARTICLE SNIPPETS and ONLY summarize information *directly related* to **crypto startups** (companies, projects, funding in the blockchain/crypto/web3 space). Ignore ALL non-crypto news (e.g., general tech, politics, mobility).\n\n"
        "**ULTRA-STRICT RULE 3: NO EXTRA TEXT.** Your response MUST contain ONLY the summary digest. Do NOT include ANY commentary, greetings, notes, self-corrections, apologies, or ANY text before or after the digest.\n\n"
        "**ROLE:** You are a professional crypto venture analyst. Tone: Insightful, objective, concise, 100% professional.\n\n"
        "**TASK:** Read the ARTICLE SNIPPETS. Create a brief, bulleted summary highlighting important developments related to **crypto startups**, focusing specifically on {prompt_focus}.\n\n"
        "**ARTICLE SNIPPETS:**\n"
        f"\"\"\"\n{combined_articles}\n\"\"\"\n\n"
        "**OUTPUT FORMAT (FOLLOW EXACTLY):**\n"
        f"- Start with the heading: `### Recent Crypto {category.capitalize()} Startup Highlights`\n"
        "- Use bullet points (`* `) for key news related ONLY to crypto startups.\n"
        "- Be factual, extract info ONLY from snippets. Keep it concise (4-6 points max).\n\n"
        "**FINAL REVIEW:** Confirm ZERO profanity. Confirm ONLY crypto startup news is included. Confirm NO extra text exists. Confirm formatting is perfect."
    )

    summary = get_dobby_response(final_prompt)
    cleaned_summary = filter_profanity(summary)

    await thinking_message.delete()
    await send_message(update, context, cleaned_summary, reply_markup=MAIN_MARKUP)

async def latest_news(update: Update, context: CallbackContext) -> None:
    await get_news_digest(update, context, category="general", prompt_focus="general news, product launches, and major partnerships")

async def funding_news(update: Update, context: CallbackContext) -> None:
    await get_news_digest(update, context, category="funding", prompt_focus="funding rounds (company, amount, investors if mentioned)")

async def defi_news(update: Update, context: CallbackContext) -> None:
    await get_news_digest(update, context, category="defi", prompt_focus="developments in DeFi startups")

async def web3gaming_news(update: Update, context: CallbackContext) -> None:
    await get_news_digest(update, context, category="web3gaming", prompt_focus="developments in Web3 Gaming startups")


# --- Main Bot Setup ---
def main() -> None:
    if not TELEGRAM_TOKEN:
        print("Error: TELEGRAM_TOKEN not found. Please set it in your .env file.")
        return

    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about))
    application.add_handler(CommandHandler("latest", latest_news))
    application.add_handler(CommandHandler("funding", funding_news))
    application.add_handler(CommandHandler("defi", defi_news))
    application.add_handler(CommandHandler("web3gaming", web3gaming_news))
    # Removed generation/style commands

    # Add a message handler to guide users if they don't use a command
    async def guide_user(update: Update, context: CallbackContext):
        # Respond only if it's likely not a button press from the main keyboard
        if update.message.text not in ["/latest", "/funding", "/defi", "/web3gaming", "/help", "/about"]:
            await send_message(update, context, "Please use one of the commands like /latest or /funding. See /help for options.", reply_markup=MAIN_MARKUP)

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, guide_user))

    print("Your Crypto Startup Pulse Bot (V1.1) is now online!")
    application.run_polling()

if __name__ == '__main__':
    main()