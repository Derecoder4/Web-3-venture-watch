# telegram_bot.py (V13.1 - Crypto Pulse + Filter + TC Feed)
import os
import requests
import feedparser # For parsing RSS feeds
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext
from bs4 import BeautifulSoup # Keep for cleaning summaries if needed

# Load the secret keys from the .env file FIRST
load_dotenv()

# --- Import Custom Modules ---
from dobby_client import get_dobby_response # Uses default max_tokens=1024, temp=0.6

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# --- Define Main Keyboard ---
MAIN_KEYBOARD = [
    ["💡 Generate New Idea"], # Changed back from Refiner
    ["📂 My Saved Ideas", "ℹ️ About"],
]
MAIN_MARKUP = ReplyKeyboardMarkup(MAIN_KEYBOARD, resize_keyboard=True)

# Keyboards for generation flow
TONE_KEYBOARD = [
    ["Shitposter", "Conversational"],
    ["Philosophical", "Researcher", "Trader"],
    ["/cancel"],
]
TONE_MARKUP = ReplyKeyboardMarkup(TONE_KEYBOARD, resize_keyboard=True, one_time_keyboard=True)

QUANTITY_KEYBOARD = [
    ["1", "2", "3"],
    ["/cancel"],
]
QUANTITY_MARKUP = ReplyKeyboardMarkup(QUANTITY_KEYBOARD, resize_keyboard=True, one_time_keyboard=True)


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
    "fuck": "f***",
    "fucking": "f***",
    "shit": "s***",
    "ass": "a**",
    "asshole": "a**hole",
    "damn": "darn",
    "bitch": "b****",
    # Add any other words you want to replace
}

def filter_profanity(text: str) -> str:
    """Replaces common profanities in the text."""
    if not isinstance(text, str):
        return str(text) if text is not None else ""

    words = text.split()
    cleaned_words = []
    for word in words:
        clean_word = word.strip('.,!?;:\'"').lower()
        replacement = FORBIDDEN_WORDS.get(clean_word)
        if replacement:
            cleaned_words.append(word.lower().replace(clean_word, replacement))
        else:
            cleaned_words.append(word)
    return " ".join(cleaned_words)


# --- Utility Function for Sending Messages (Simple Split) ---
async def send_message(update: Update, context: CallbackContext, text: str, reply_markup=None):
    """Sends a message, splitting it simply by character limit if needed."""
    MAX_MESSAGE_LENGTH = 4096
    if not text:
        print("Warning: Attempted to send empty message.")
        await update.message.reply_text("Sorry, I couldn't generate a response for that.", reply_markup=reply_markup)
        return

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
    combined_text = ""
    urls_to_fetch = FEED_URLS.get(category, [])
    if not urls_to_fetch:
        return "Error: No RSS feeds configured for this category."

    print(f"Fetching feeds for category: {category}")
    articles_found = 0
    for url in urls_to_fetch:
        try:
            feed = feedparser.parse(url)
            entries = feed.entries[:num_articles]
            for entry in entries:
                articles_found += 1
                title = entry.get('title', 'No Title')
                summary = entry.get('summary', entry.get('description', ''))
                # Clean summary
                summary_text = requests.utils.unquote(summary)
                if '<' in summary_text:
                     soup = BeautifulSoup(summary_text, 'html.parser')
                     summary_text = soup.get_text(separator=' ', strip=True)

                combined_text += f"Title: {title}\nSummary: {summary_text}\n---\n"
                if len(combined_text) > 4000: break # Limit text sent to AI
            if len(combined_text) > 4000: break
        except Exception as e:
            print(f"Error fetching/parsing feed {url}: {e}")
            continue

    if articles_found == 0:
        return "No recent articles found in the feeds for this category."
    elif not combined_text:
         return "Found articles, but could not extract summaries."
    else:
        return combined_text[:4000]


# --- Command Handlers ---

async def start(update: Update, context: CallbackContext) -> None:
    # Changed back to generation focus
    welcome_text = (
        "Hi! I'm your AI Content Strategist, powered by Dobby.\n\n"
        "Tap '💡 Generate New Idea' or send me a topic to get started.\n\n"
        "Use `/setstyle` to teach me your voice, or use news commands like `/latest`, `/funding`."
    )
    await send_message(update, context, welcome_text, reply_markup=MAIN_MARKUP)

async def help_command(update: Update, context: CallbackContext) -> None:
    # Updated help text combining generation and news
    help_text = (
        "**Content Generation:**\n"
        "1. Send a topic (or tap '💡 Generate New Idea').\n"
        "2. Choose Tone & Quantity (or use custom style).\n"
        "   `/setstyle [example]` - Teach me your style.\n"
        "   `/clearstyle` - Reset to default tones.\n"
        "   `/generatethread` - (Legacy) Start generation.\n\n"
        "**Crypto Startup News:**\n"
        "/latest - General startup news digest\n"
        "/funding - Recent funding rounds digest\n"
        "/defi - DeFi startup news digest\n"
        "/web3gaming - Web3 Gaming startup news digest\n\n"
        "**Other:**\n"
        "/about - Info about me\n"
        "/cancel - Stop current action"
    )
    await send_message(update, context, help_text, reply_markup=MAIN_MARKUP)

async def about(update: Update, context: CallbackContext) -> None:
    about_text = (
        "Your AI analyst & content strategist for crypto startups.\n"
        "Uses Dobby via Fireworks AI. Bot by @joshehh for Sentient."
    )
    await send_message(update, context, about_text, reply_markup=MAIN_MARKUP)

async def my_ideas(update: Update, context: CallbackContext) -> None:
    await send_message(update, context,
        "This feature is coming soon! This will allow you to save your best-generated ideas.",
        reply_markup=MAIN_MARKUP
    )

async def cancel(update: Update, context: CallbackContext) -> None:
    context.user_data.clear()
    await send_message(update, context,
        "Process cancelled. What's next?",
        reply_markup=MAIN_MARKUP
    )

async def set_style_command(update: Update, context: CallbackContext) -> None:
    style_example = " ".join(context.args)
    if not style_example or len(style_example) < 10:
        await send_message(update, context,
            "Please provide example text after the command.\n"
            "Example: `/setstyle Your example tweet text here...`"
        )
        return
    context.user_data['custom_style'] = style_example
    await send_message(update, context,
        "✅ Style saved! I'll use this for future thread generations.\n"
        "Use /clearstyle to remove it.",
        reply_markup=MAIN_MARKUP
    )

async def clear_style(update: Update, context: CallbackContext) -> None:
    if 'custom_style' in context.user_data:
        del context.user_data['custom_style']
        await send_message(update, context, "🗑️ Custom style cleared.", reply_markup=MAIN_MARKUP)
    else:
        await send_message(update, context, "No custom style was set.", reply_markup=MAIN_MARKUP)

# --- News Digest Commands ---

async def get_news_digest(update: Update, context: CallbackContext, category: str, prompt_focus: str):
    """Generic function to handle fetching, summarizing, and sending digests."""
    thinking_message = await update.message.reply_text(f"📰 Fetching latest {category} news...", reply_markup=MAIN_MARKUP)

    combined_articles = fetch_and_combine_feeds(category)

    if combined_articles.startswith("Error:") or combined_articles.startswith("No recent") or combined_articles.startswith("Found articles, but"):
        await thinking_message.delete()
        await send_message(update, context, combined_articles, reply_markup=MAIN_MARKUP)
        return

    final_prompt = (
        "**ROLE:** You are a crypto venture analyst. Your tone is professional, insightful, and concise. NO PROFANITY.\n\n"
        "**TASK:** Read the following snippets from recent crypto/tech news articles. Create a brief, bulleted summary highlighting the most important developments related to **crypto startups**, focusing specifically on {prompt_focus}.\n\n"
        "**ARTICLE SNIPPETS:**\n"
        f"\"\"\"\n{combined_articles}\n\"\"\"\n\n"
        "**OUTPUT:**\n"
        f"- Start with a heading like '### Recent Crypto {category.capitalize()} Startup Highlights'\n"
        "- Use bullet points for key news (e.g., funding rounds, major launches, notable partnerships related to crypto startups ONLY).\n"
        "- Be factual and extract information ONLY from the provided snippets. Ignore non-crypto news.\n"
        "- Keep the summary concise (around 4-6 key bullet points total)."
    )

    summary = get_dobby_response(final_prompt)
    cleaned_summary = filter_profanity(summary) # Apply the filter

    await thinking_message.delete()
    await send_message(update, context, cleaned_summary, reply_markup=MAIN_MARKUP) # Send cleaned


async def latest_news(update: Update, context: CallbackContext) -> None:
    await get_news_digest(update, context, category="general", prompt_focus="general news, product launches, and major partnerships")

async def funding_news(update: Update, context: CallbackContext) -> None:
    await get_news_digest(update, context, category="funding", prompt_focus="funding rounds (company, amount, investors if mentioned)")

async def defi_news(update: Update, context: CallbackContext) -> None:
    await get_news_digest(update, context, category="defi", prompt_focus="developments in DeFi startups")

async def web3gaming_news(update: Update, context: CallbackContext) -> None:
    await get_news_digest(update, context, category="web3gaming", prompt_focus="developments in Web3 Gaming startups")


# --- Conversation & Message Handler (Thread Generation V15 Prompt) ---
async def handle_message(update: Update, context: CallbackContext) -> None:
    text = update.message.text
    state = context.user_data.get('state')

    # --- 1. Handle Main Menu Buttons / Initial Input ---
    if not state:
        # Check if text matches a news command button
        if text == "/latest": await latest_news(update, context); return
        if text == "/funding": await funding_news(update, context); return
        if text == "/defi": await defi_news(update, context); return
        if text == "/web3gaming": await web3gaming_news(update, context); return
        if text == "/help": await help_command(update, context); return
        if text == "/about": await about(update, context); return

        # Handle Generation buttons
        if text == "💡 Generate New Idea":
            await send_message(update, context, "Great! What's the topic?", reply_markup=ReplyKeyboardRemove())
            context.user_data['state'] = 'AWAITING_TOPIC'
            return
        elif text == "📂 My Saved Ideas":
            await my_ideas(update, context)
            return
        elif text == "ℹ️ About": # Duplicate check, but safe
            await about(update, context)
            return

        # Assume text is a topic for generation
        context.user_data['topic'] = text
        custom_style = context.user_data.get('custom_style')
        if custom_style:
            await send_message(update, context, f"Using your custom style for '{text}'. How many threads (1-3)?", reply_markup=QUANTITY_MARKUP)
            context.user_data['state'] = 'AWAITING_QUANTITY'
        else:
            await send_message(update, context, "Got it. What tone should I use?", reply_markup=TONE_MARKUP)
            context.user_data['state'] = 'AWAITING_TONE'
        return

    # --- 2. Handle Conversation States ---
    if state == 'AWAITING_TOPIC':
        context.user_data['topic'] = text
        custom_style = context.user_data.get('custom_style')
        if custom_style:
            await send_message(update, context, f"Using your custom style for '{text}'. How many threads (1-3)?", reply_markup=QUANTITY_MARKUP)
            context.user_data['state'] = 'AWAITING_QUANTITY'
        else:
            await send_message(update, context, "Perfect. Now, what tone should I use?", reply_markup=TONE_MARKUP)
            context.user_data['state'] = 'AWAITING_TONE'
        return

    elif state == 'AWAITING_TONE':
        if text not in ["Shitposter", "Conversational", "Philosophical", "Researcher", "Trader"]:
            await send_message(update, context, "Please select a valid tone from the keyboard.", reply_markup=TONE_MARKUP)
            return
        context.user_data['tone'] = text
        await send_message(update, context, "Nice. And how many threads should I generate (1-3)?", reply_markup=QUANTITY_MARKUP)
        context.user_data['state'] = 'AWAITING_QUANTITY'
        return

    elif state == 'AWAITING_QUANTITY':
        try:
            quantity = int(text)
            if not 1 <= quantity <= 3: raise ValueError
        except ValueError:
            await send_message(update, context, "Please select a valid quantity (1, 2, or 3).", reply_markup=QUANTITY_MARKUP)
            return

        context.user_data['quantity'] = quantity
        topic = context.user_data['topic']
        tone = context.user_data.get('tone')
        custom_style = context.user_data.get('custom_style')

        tone_or_style_desc = f"'{tone}' tone" if tone else "your custom style"
        await update.message.reply_text(
            f"🤖 Okay, generating {quantity} thread(s) about '{topic}' using {tone_or_style_desc}. Please wait...",
            reply_markup=MAIN_MARKUP
        )

        # --- Prompt Build Logic (V15) ---
        if custom_style:
            style_instruction = f"**STYLE GUIDE:** Mimic this style:\n\"\"\"\n{custom_style}\n\"\"\"\n"
            profanity_rule = "**ULTRA-STRICT RULE: Your response MUST NOT contain ANY vulgarity or profanity. Absolutely none.**\n\n"
        else:
            tone_description = ""
            if tone == "Shitposter":
                tone_description = "Witty, edgy, provocative, informal. Strong opinions. (Profanity allowed ONLY for this tone)."
                profanity_rule = "**RULE: Profanity is allowed ONLY because the selected tone is 'Shitposter'.**\n\n"
            # (Keep elif blocks for other tones, ensuring they set the ULTRA-STRICT profanity_rule)
            elif tone == "Conversational":
                tone_description = "Friendly, approachable, easy to read. **Absolutely NO profanity.**"
                profanity_rule = "**ULTRA-STRICT RULE: Your response MUST NOT contain ANY vulgarity or profanity. Absolutely none.**\n\n"
            elif tone == "Philosophical":
                tone_description = "Deep, abstract, thought-provoking. **Formal language. Absolutely NO profanity.**"
                profanity_rule = "**ULTRA-STRICT RULE: Your response MUST NOT contain ANY vulgarity or profanity. Absolutely none.**\n\n"
            elif tone == "Researcher":
                tone_description = "Data-driven, objective, analytical. **Formal language. Absolutely NO profanity.**"
                profanity_rule = "**ULTRA-STRICT RULE: Your response MUST NOT contain ANY vulgarity or profanity. Absolutely none.**\n\n"
            elif tone == "Trader":
                tone_description = "Action-oriented, concise, market-focused. **Professional tone. Absolutely NO profanity.**"
                profanity_rule = "**ULTRA-STRICT RULE: Your response MUST NOT contain ANY vulgarity or profanity. Absolutely none.**\n\n"

            style_instruction = f"**TONE:** Write STRICTLY in this tone: **{tone_description}**"

        # --- V15 PROMPT ---
        final_prompt = (
            f"{profanity_rule}"
            f"**TASK DEFINITION:**\n"
            f"- **Topic:** '{topic}'\n"
            f"- **Quantity:** You MUST generate EXACTLY {quantity} thread(s). NO MORE, NO LESS.\n\n"
            f"**IMPERATIVE RULES (NON-NEGOTIABLE):**\n"
            f"1.  **No Extra Text:** Your entire response MUST consist ONLY of the generated thread(s). Do NOT include ANY introductory sentences, commentary, notes, titles (unless part of the first tweet), review markers, or concluding remarks before, between, or after the threads.\n"
            f"2.  **Focus:** Generate content ONLY about the specified Topic ('{topic}').\n"
            f"3.  **Length:** Each thread MUST have EXACTLY 8 tweets (1/8 to 8/8). STOP WRITING after the 8th tweet for each thread.\n"
            f"4.  **Completeness:** Ensure each tweet and thread is fully written.\n\n"
            f"**INSTRUCTIONS:**\n"
            f"You are an AI generating Twitter threads.\n"
            f"1.  {style_instruction}\n"
            f"2.  **CONTENT:** Write insightful paragraphs for each tweet. No bullet points.\n"
            f"3.  **FORMATTING (MUST FOLLOW EXACTLY):**\n"
            f"    - Start each tweet with 'X/8: ' (e.g., '1/8: ', '2/8: ', ... '8/8: ').\n"
            f"    - **Separate each tweet with TWO new lines (`\\n\\n`).** Example:\n" # V16 Fix included
            f"      1/8: [Text of first tweet]\n\n" # Explicit example
            f"      2/8: [Text of second tweet]\n\n" # Explicit example
            f"    - If generating >1 thread (and ONLY if requested quantity > 1), separate them with '--- THREAD 2 ---', '--- THREAD 3 ---'.\n"
            f"    - Include relevant hashtags (#example) at the end of some tweets.\n\n"
            f"**FINAL CHECK:** Ensure ZERO forbidden profanity (unless 'Shitposter'). Ensure EXACT quantity ({quantity}). Ensure EXACT length (8 tweets). Ensure correct **DOUBLE newline** formatting. Ensure ABSOLUTELY NO TEXT exists outside the requested thread(s)."
        )
        # --- END OF V15 PROMPT ---

        response = get_dobby_response(final_prompt) # Uses default max_tokens
        cleaned_response = filter_profanity(response) # Apply filter to generation too

        await send_message(update, context, cleaned_response, reply_markup=MAIN_MARKUP) # Send cleaned

        context.user_data.clear()
        return

# --- Main Bot Setup ---
def main() -> None:
    if not TELEGRAM_TOKEN:
        print("Error: TELEGRAM_TOKEN not found. Please set it in your .env file.")
        return

    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Register command handlers (including news commands)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about))
    application.add_handler(CommandHandler("myideas", my_ideas))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(CommandHandler("generatethread", handle_message))
    application.add_handler(CommandHandler("latest", latest_news))
    application.add_handler(CommandHandler("funding", funding_news))
    application.add_handler(CommandHandler("defi", defi_news))
    application.add_handler(CommandHandler("web3gaming", web3gaming_news))
    application.add_handler(CommandHandler("setstyle", set_style_command))
    application.add_handler(CommandHandler("clearstyle", clear_style))

    # Register the main message handler (must be last text handler)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Your AI Content Bot (V13.1 - News & Gen + Filter) is now online!")
    application.run_polling()

if __name__ == '__main__':
    main()