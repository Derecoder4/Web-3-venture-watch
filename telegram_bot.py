# telegram_bot.py
import os
import requests # Make sure 'requests' is imported at the top
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext

# Load the secret keys from the .env file FIRST
load_dotenv()

# --- Import Custom Modules ---
from dobby_client import get_dobby_response

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# --- Define Keyboards ---
# Main menu
MAIN_KEYBOARD = [
    ["💡 Generate New Idea"],
    ["📂 My Saved Ideas", "ℹ️ About"],
]
MAIN_MARKUP = ReplyKeyboardMarkup(MAIN_KEYBOARD, resize_keyboard=True)

# Tone selection
TONE_KEYBOARD = [
    ["Shitposter", "Conversational"],
    ["Philosophical", "Researcher", "Trader"],
    ["/cancel"],
]
TONE_MARKUP = ReplyKeyboardMarkup(TONE_KEYBOARD, resize_keyboard=True, one_time_keyboard=True)

# Quantity selection
QUANTITY_KEYBOARD = [
    ["1", "2", "3"],
    ["/cancel"],
]
QUANTITY_MARKUP = ReplyKeyboardMarkup(QUANTITY_KEYBOARD, resize_keyboard=True, one_time_keyboard=True)

# --- Command Handlers ---

async def start(update: Update, context: CallbackContext) -> None:
    """Sends a welcome message and the main keyboard."""
    context.user_data.clear()
    welcome_text = (
        "Hi! I'm your AI Content Strategist, powered by Dobby.\n\n"
        "Tap '💡 Generate New Idea' or send me a topic to get started.\n\n"
        "You can also use `/trending` to get live market info."
    )
    await update.message.reply_text(welcome_text, reply_markup=MAIN_MARKUP)

async def help_command(update: Update, context: CallbackContext) -> None:
    """Sends a helpful message."""
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
    """Sends the 'About' message."""
    about_text = (
        "This is an AI bot built by @josh_ehh for the Sentient Builder Program.\n\n"
        "It uses the **Dobby model** via the Fireworks AI API to help you brainstorm content ideas."
    )
    await update.message.reply_text(about_text, reply_markup=MAIN_MARKUP)

async def my_ideas(update: Update, context: CallbackContext) -> None:
    """Placeholder for the 'My Saved Ideas' feature."""
    await update.message.reply_text(
        "This feature is coming soon! This will allow you to save and view your best-generated ideas.",
        reply_markup=MAIN_MARKUP
    )

async def cancel(update: Update, context: CallbackContext) -> None:
    """Cancels the current conversation state."""
    context.user_data.clear()
    await update.message.reply_text(
        "Process cancelled. What's next?",
        reply_markup=MAIN_MARKUP
    )

# --- NEW COMMAND ---
async def trending(update: Update, context: CallbackContext) -> None:
    """Gets top 7 trending coins from CoinGecko and has Dobby analyze them."""
    await update.message.reply_text("🔥 Getting CoinGecko's top 7 trending... one sec.")
    
    try:
        # 1. Call the CoinGecko API
        url = "https://api.coingecko.com/api/v3/search/trending"
        response = requests.get(url)
        response.raise_for_status()
        
        data = response.json()
        trending_coins = data.get('coins', [])
        
        if not trending_coins:
            await update.message.reply_text("Sorry, I couldn't fetch the trending list.")
            return

        # 2. Create a clean list of coin names
        coin_names = [coin['item']['name'] for coin in trending_coins]
        coin_list = ", ".join(coin_names)

        # 3. Build the Dobby prompt
        final_prompt = (
            "You are a 'Trader' tone AI. You are an expert at market analysis. "
            "Based *only* on the fact that these are the **top 7 trending projects on CoinGecko**, "
            "give me a brief, insightful market commentary. Why might these be trending?\n\n"
            f"**Trending List:** {coin_list}\n\n"
            "Keep it concise and actionable."
        )

        # 4. Get Dobby's analysis
        analysis = get_dobby_response(final_prompt)
        await update.message.reply_text(analysis, reply_markup=MAIN_MARKUP)

    except requests.exceptions.RequestException as e:
        print(f"CoinGecko API error: {e}")
        await update.message.reply_text("Sorry, I had trouble connecting to the CoinGecko API.")

# --- Conversation & Message Handler ---

async def handle_message(update: Update, context: CallbackContext) -> None:
    """Handles all text messages and routes them based on state."""
    text = update.message.text
    state = context.user_data.get('state')

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
        
        context.user_data['topic'] = text
        await update.message.reply_text("Got it. What tone should I use?", reply_markup=TONE_MARKUP)
        context.user_data['state'] = 'AWAITING_TONE'
        return

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
            tone_description = "Witty, edgy, provocative, and informal. Use strong, contrarian opinions. (Avoid constant, low-effort profanity; be clever)."
        elif tone == "Conversational":
            tone_description = "Friendly, approachable, and easy to read, as if explaining to a friend."
        elif tone == "Philosophical":
            tone_description = "Deep, abstract, and thought-provoking. Focus on the 'why' and the bigger picture."
        elif tone == "Researcher":
            tone_description = "Data-driven, objective, and analytical. Use formal language and cite concepts (hypothetically)."
        elif tone == "Trader":
            tone_description = "Action-oriented, concise, and focused on market impact, price action, and potential opportunities."

        final_prompt = (
            f"You are an expert content creator. A user wants you to generate {context.user_data['quantity']} "
            f"ready-to-post Twitter threads about the topic: '{context.user_data['topic']}'.\n\n"
            f"**CRITICAL INSTRUCTIONS:**\n\n"
            f"1.  **TONE:** You MUST write in the following tone: **{tone_description}**\n\n"
            f"2.  **CONTENT:** Do NOT use bullet points. Write out the full text of the thread(s) with deep insights, analysis, and opinions. Each tweet should be a full paragraph.\n\n"
            f"3.  **FORMATTING (VERY IMPORTANT):**\n"
            f"    - Each thread must have 6-8 tweets.\n"
            f"    - **Separate each individual tweet (e.g., 1/8, 2/8) with a new line.** This is crucial for readability.\n"
            f"    - If generating more than one thread, separate them with a clear marker like '--- THREAD 2 ---'.\n"
            f"    - Include relevant hashtags at the end of some tweets."
        )

        response = get_dobby_response(final_prompt)
        await update.message.reply_text(response, reply_markup=MAIN_MARKUP)
        
        context.user_data.clear()
        return

# --- Main Bot Setup ---

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
    application.add_handler(CommandHandler("generatethread", handle_message))
    application.add_handler(CommandHandler("trending", trending)) # <-- New command
    
    # Register the main message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Your AI Content Strategist (V4.1) is now online!")
    application.run_polling()

if __name__ == '__main__':
    main()