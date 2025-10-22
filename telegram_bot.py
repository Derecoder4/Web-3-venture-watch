# telegram_bot.py
import os
import requests # Make sure 'requests' is imported
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext

# Load the secret keys from the .env file FIRST
load_dotenv()

# --- Import Custom Modules ---
from dobby_client import get_dobby_response

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# --- Define Keyboards ---
MAIN_KEYBOARD = [
    ["💡 Generate New Idea"],
    ["📂 My Saved Ideas", "ℹ️ About"],
]
MAIN_MARKUP = ReplyKeyboardMarkup(MAIN_KEYBOARD, resize_keyboard=True)

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

# --- Command Handlers ---

async def start(update: Update, context: CallbackContext) -> None:
    context.user_data.clear()
    welcome_text = (
        "Hi! I'm your AI Content Strategist, powered by Dobby.\n\n"
        "Tap '💡 Generate New Idea' or send me a topic to get started.\n\n"
        "You can also use `/trending` to get live market info."
    )
    await update.message.reply_text(welcome_text, reply_markup=MAIN_MARKUP)

async def help_command(update: Update, context: CallbackContext) -> None:
    help_text = (
        "Here's how to use me:\n\n"
        "1.  **Just send a topic:** I'll ask you for the tone and quantity.\n"
        "2.  **/trending**: Get AI analysis on CoinGecko's top 7.\n"
        "3.  **/generatethread**: (Legacy) Starts the guided process.\n"
        "4.  **/myideas**: (Coming Soon) View your saved ideas.\n"
        "5.  **/about**: Learn about this bot.\n"
        "6.  **/cancel**: Use this anytime to stop the idea generation process."
    )
    await update.message.reply_text(help_text, reply_markup=MAIN_MARKUP)

async def about(update: Update, context: CallbackContext) -> None:
    about_text = (
        "This is an AI bot built by @josh_ehh for the Sentient Builder Program.\n\n"
        "It uses the **Dobby model** via the Fireworks AI API to help you brainstorm content ideas."
    )
    await update.message.reply_text(about_text, reply_markup=MAIN_MARKUP)

async def my_ideas(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "This feature is coming soon! This will allow you to save and view your best-generated ideas.",
        reply_markup=MAIN_MARKUP
    )

async def cancel(update: Update, context: CallbackContext) -> None:
    context.user_data.clear()
    await update.message.reply_text(
        "Process cancelled. What's next?",
        reply_markup=MAIN_MARKUP
    )

async def trending(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("🔥 Getting CoinGecko's top 7 trending... one sec.")
    
    try:
        url = "https://api.coingecko.com/api/v3/search/trending"
        response = requests.get(url)
        response.raise_for_status()
        
        data = response.json()
        trending_coins = data.get('coins', [])
        
        if not trending_coins:
            await update.message.reply_text("Sorry, I couldn't fetch the trending list.")
            return

        coin_names = [coin['item']['name'] for coin in trending_coins]
        coin_list = ", ".join(coin_names)

        final_prompt = (
            "**ABSOLUTE RULE: You MUST NOT use any profanity (e.g., 'fuck', 'shit', 'bitch', 'ass') in your response.**\n\n"
            "You are a professional crypto market analyst (like Bloomberg). Your tone is insightful, objective, professional, and concise.\n\n"
            f"The top 7 trending projects on CoinGecko are: {coin_list}\n\n"
            "**YOUR TASK:**\n"
            "Create a formatted report. For EACH of the 7 projects, provide EXACTLY these three points:\n"
            "1.  **Analysis:** (1 sentence) Insight on why it might be trending.\n"
            "2.  **Sentiment:** (1 word: Bullish / Bearish / Neutral)\n"
            "3.  **Actionable Insight:** (1 short phrase for traders)\n\n"
            "**FORMATTING RULES (VERY IMPORTANT - FOLLOW EXACTLY):**\n"
            "   - Start with the heading '### Trending Market Analysis'\n"
            "   - Use a relevant emoji and **bold the coin name** for each project (e.g., '🚀 **Bitcoin**').\n"
            "   - **Use a bulleted list (`*`) for the 3 points under each coin.**\n"
            "   - **Add TWO blank lines between each coin's analysis** for clear spacing.\n"
            "   - After the list, add a 2-sentence market summary starting with 'Overall Sentiment:'.\n\n"
            "**Example Structure for ONE coin:**\n"
            "🚀 **Coin Name**\n"
            "* Analysis: [Your one-sentence analysis here].\n"
            "* Sentiment: [Bullish/Bearish/Neutral].\n"
            "* Actionable Insight: [Your short phrase here].\n\n\n" # Two blank lines
        )

        analysis = get_dobby_response(final_prompt)
        await update.message.reply_text(analysis, reply_markup=MAIN_MARKUP)

    except requests.exceptions.RequestException as e:
        print(f"CoinGecko API error: {e}")
        await update.message.reply_text("Sorry, I had trouble connecting to the CoinGecko API.")

# --- Conversation & Message Handler ---
# Make sure this function definition is NOT indented inside another function
async def handle_message(update: Update, context: CallbackContext) -> None:
    """Handles all text messages and routes them based on state."""
    text = update.message.text
    state = context.user_data.get('state')

    # --- 1. Handle Main Menu Buttons ---
    if not state:
        if text == "💡 Generate New Idea":
            await update.message.reply_text("Great! What's the topic?", reply_markup=ReplyKeyboardRemove())
            context.user_data['state'] = 'AWAITING_TOPIC'
            return
        elif text == "📂 My Saved Ideas":
            await my_ideas(update, context)
            return
        elif text == "ℹ️ About":
            await about(update, context)
            return
        
        # If no state and not a button, treat it as a new topic
        context.user_data['topic'] = text
        await update.message.reply_text("Got it. What tone should I use?", reply_markup=TONE_MARKUP)
        context.user_data['state'] = 'AWAITING_TONE'
        return

    # --- 2. Handle Conversation States ---
    if state == 'AWAITING_TOPIC':
        context.user_data['topic'] = text
        await update.message.reply_text("Perfect. Now, what tone should I use?", reply_markup=TONE_MARKUP)
        context.user_data['state'] = 'AWAITING_TONE'
        return

    elif state == 'AWAITING_TONE':
        if text not in ["Shitposter", "Conversational", "Philosophical", "Researcher", "Trader"]:
            await update.message.reply_text("Please select a valid tone from the keyboard.", reply_markup=TONE_MARKUP)
            return
        
        context.user_data['tone'] = text
        await update.message.reply_text("Nice. And how many threads should I generate (1-3)?", reply_markup=QUANTITY_MARKUP)
        context.user_data['state'] = 'AWAITING_QUANTITY'
        return
        
    elif state == 'AWAITING_QUANTITY':
        try:
            quantity = int(text)
            if not 1 <= quantity <= 3:
                raise ValueError
        except ValueError:
            await update.message.reply_text("Please select a valid quantity (1, 2, or 3).", reply_markup=QUANTITY_MARKUP)
            return

        context.user_data['quantity'] = quantity
        await update.message.reply_text(
            f"🤖 Got it. Generating {quantity} thread(s) about '{context.user_data['topic']}' in a '{context.user_data['tone']}' tone...",
            reply_markup=MAIN_MARKUP
        )
        
        tone = context.user_data['tone']
        tone_description = ""
        if tone == "Shitposter":
            tone_description = "Witty, edgy, provocative, and informal. Use strong, contrarian opinions. (Profanity like 'fuck' or 'shit' is allowed for this tone ONLY)."
        elif tone == "Conversational":
            tone_description = "Friendly, approachable, and easy to read. **Must be 100% professional and use zero profanity.**"
        elif tone == "Philosophical":
            tone_description = "Deep, abstract, and thought-provoking. **Must use formal, academic language and zero profanity.**"
        elif tone == "Researcher":
            tone_description = "Data-driven, objective, and analytical. **Must use formal, academic language and zero profanity.**"
        elif tone == "Trader":
            tone_description = "Action-oriented, concise, and focused on market impact. **Must be 100% professional and use zero profanity.**"

        final_prompt = (
            "**ABSOLUTE RULE: You MUST NOT use any profanity (e.g., 'fuck', 'shit', 'bitch', 'ass') UNLESS the user's selected tone is EXACTLY 'Shitposter'. For all other tones, your response must be 100% professional.**\n\n"
            f"You are an expert content creator. Generate {context.user_data['quantity']} "
            f"ready-to-post Twitter threads about the topic: '{context.user_data['topic']}'.\n\n"
            f"**CRITICAL INSTRUCTIONS:**\n\n"
            f"1.  **TONE:** Write EXACTLY in this tone: **{tone_description}**\n\n"
            f"2.  **CONTENT:** Do NOT use bullet points. Write full paragraphs for each tweet, providing deep insights.\n\n"
            f"3.  **FORMATTING (FOLLOW EXACTLY):**\n"
            f"    - Each thread must have 6-8 tweets.\n"
            f"    - **Separate each individual tweet (e.g., 1/8, 2/8) with ONE new line.**\n"
            f"    - If generating >1 thread, separate them with '--- THREAD 2 ---'.\n"
            f"    - Include relevant hashtags at the end of some tweets."
        )

        response = get_dobby_response(final_prompt)
        await update.message.reply_text(response, reply_markup=MAIN_MARKUP)
        
        context.user_data.clear()
        return

# --- Main Bot Setup ---
# Make sure this function definition is NOT indented inside another function
def main() -> None:
    """Start the bot."""
    if not TELEGRAM_TOKEN:
        print("Error: TELEGRAM_TOKEN not found. Please set it in your .env file.")
        return

    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Register all command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about))
    application.add_handler(CommandHandler("myideas", my_ideas))
    application.add_handler(CommandHandler("cancel", cancel))
    # Both of these lines need the correct 'handle_message' name
    application.add_handler(CommandHandler("generatethread", handle_message))
    application.add_handler(CommandHandler("trending", trending))
    
    # Register the main message handler - this also needs the correct name
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Your AI Content Strategist (V6) is now online!")
    application.run_polling()

# Make sure this line is NOT indented
if __name__ == '__main__':
    main()