# telegram_bot.py (V1 - Crypto Startup Pulse)
import os
import requests
import feedparser # For parsing RSS feeds
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup # Keep ReplyKeyboardMarkup for potential future buttons
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext

# Load the secret keys from the .env file FIRST
load_dotenv()

# --- Import Custom Modules ---
from dobby_client import get_dobby_response # Uses default max_tokens=1024, temp=0.6

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# --- Define Main Keyboard (Optional, can add buttons later) ---
MAIN_KEYBOARD = [
    ["/latest", "/funding"],
    ["/defi", "/web3gaming"],
    ["/help", "/about"],
]
MAIN_MARKUP = ReplyKeyboardMarkup(MAIN_KEYBOARD, resize_keyboard=True)

# --- RSS Feed Configuration ---
# Example Feeds (Replace with actual, relevant RSS URLs after searching)
# Need feeds that focus on startups, funding, specific sectors (DeFi, Gaming)
# Use Google Search results from previous turn to find actual URLs
FEED_URLS = {
    "general": [
        "https://cointelegraph.com/rss/tag/startups", # Example Cointelegraph Startups Feed
        "https://decrypt.co/feed",                  # Example Decrypt General Feed (Needs Filtering)
        "https://blockworks.co/feed",               # Example Blockworks Feed
        "https://www.coindesk.com/arc/outboundfeeds/rss/", # Example CoinDesk General Feed
        # Add more relevant feeds...
    ],
    "funding": [
        "https://cointelegraph.com/rss/tag/funding", # Example Cointelegraph Funding Feed
        "https://theblock.co/rss.xml",             # Example The Block General Feed (Needs Filtering)
        # Add feeds known for funding news...
    ],
    "defi": [
        "https://cointelegraph.com/rss/tag/defi",    # Example Cointelegraph DeFi Feed
        "https://thedefiant.io/feed",               # Example The Defiant Feed
        # Add more DeFi focused feeds...
    ],
    "web3gaming": [
        "https://cointelegraph.com/rss/tag/gaming", # Example Cointelegraph Gaming Feed
        "https://decrypt.co/feed/gaming",          # Example Decrypt Gaming Feed
        # Add more Web3 Gaming feeds...
    ]
}

# --- Utility Function for Sending Messages (Simple Split) ---
async def send_message(update: Update, context: CallbackContext, text: str, reply_markup=None):
    """Sends a message, splitting it simply by character limit if needed."""
    MAX_MESSAGE_LENGTH = 4096
    if not text:
        print("Warning: Attempted to send empty message.")
        await update.message.reply_text("Sorry, I couldn't generate a response for that.", reply_markup=reply_markup)
        return
    # Default to main keyboard if none provided
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
            # Send keyboard ONLY on the very last part
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
    combined_text = ""
    urls_to_fetch = FEED_URLS.get(category, [])
    if not urls_to_fetch:
        return "Error: No RSS feeds configured for this category."

    print(f"Fetching feeds for category: {category}")
    for url in urls_to_fetch:
        try:
            feed = feedparser.parse(url)
            # Limit to the most recent articles per feed
            entries = feed.entries[:num_articles]
            for entry in entries:
                title = entry.get('title', 'No Title')
                # Try getting 'summary' or 'description', fallback to empty
                summary = entry.get('summary', entry.get('description', ''))
                # Clean summary (basic HTML tag removal if needed, feedparser often handles this)
                summary_text = requests.utils.unquote(summary) # Handle URL encoding
                if '<' in summary_text: # Basic check for HTML
                     from bs4 import BeautifulSoup
                     soup = BeautifulSoup(summary_text, 'html.parser')
                     summary_text = soup.get_text()

                combined_text += f"Title: {title}\nSummary: {summary_text}\n---\n"
                if len(combined_text) > 4000: # Limit text sent to AI
                    break
            if len(combined_text) > 4000:
                 break
        except Exception as e:
            print(f"Error fetching/parsing feed {url}: {e}")
            continue # Skip faulty feeds

    return combined_text[:4000] if combined_text else "No recent articles found in the feeds for this category."

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
    
    # 1. Fetch and combine RSS feed text
    combined_articles = fetch_and_combine_feeds(category)

    if combined_articles.startswith("Error:") or combined_articles.startswith("No recent"):
        await thinking_message.delete()
        await send_message(update, context, combined_articles, reply_markup=MAIN_MARKUP)
        return

    # 2. Build the summarization prompt
    final_prompt = (
        "**ROLE:** You are a crypto venture analyst. Your tone is professional, insightful, and concise. NO PROFANITY.\n\n"
        "**TASK:** Read the following snippets from recent crypto news articles. Create a brief, bulleted summary highlighting the most important developments related to **crypto startups**, focusing on {prompt_focus}.\n\n"
        "**ARTICLE SNIPPETS:**\n"
        f"\"\"\"\n{combined_articles}\n\"\"\"\n\n"
        "**OUTPUT:**\n"
        "- Start with a heading like '### Recent [Category] Startup Highlights'\n"
        "- Use bullet points for key news (e.g., funding rounds, major launches, notable partnerships).\n"
        "- Be factual and extract information ONLY from the provided snippets.\n"
        "- Keep the summary concise (around 4-6 key bullet points total)."
    )

    # 3. Get Dobby's summary
    summary = get_dobby_response(final_prompt) # Uses default max_tokens & temp

    # 4. Send the summary
    await thinking_message.delete()
    await send_message(update, context, summary, reply_markup=MAIN_MARKUP)


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
    # Add a simple message handler to guide users if they don't use a command
    async def guide_user(update: Update, context: CallbackContext):
        await send_message(update, context, "Please use one of the commands like /latest or /funding. See /help for options.", reply_markup=MAIN_MARKUP)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, guide_user))


    print("Your Crypto Startup Pulse Bot is now online!")
    application.run_polling()

if __name__ == '__main__':
    main()