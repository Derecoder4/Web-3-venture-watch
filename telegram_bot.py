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

# --- Trending Command (V7 Prompt) ---
async def trending(update: Update, context: CallbackContext) -> None:
    """Gets top 7 trending coins from CoinGecko and has Dobby analyze them."""
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

        # --- V7 PROMPT FOR /trending ---
        final_prompt = (
            "**IMPERATIVE RULE:** Your entire response MUST be 100% professional and contain ZERO profanity (no 'fuck', 'shit', 'ass', etc.). Absolutely none.\n\n"
            "You are a professional crypto market analyst (like Bloomberg). Your tone is insightful, objective, and concise.\n\n"
            f"The top 7 trending projects on CoinGecko are: {coin_list}\n\n"
            "**YOUR TASK:** Create a structured market report.\n\n"
            "**PART 1: INDIVIDUAL ANALYSIS**\n"
            "For EACH of the 7 projects, provide EXACTLY these three points in a bulleted list:\n"
            "* **Analysis:** (1 sentence) Insight on why it might be trending.\n"
            "* **Sentiment:** (1 word: Bullish / Bearish / Neutral)\n"
            "* **Actionable Insight:** (1 short phrase for traders)\n\n"
            "**PART 2: OVERALL SUMMARY**\n"
            "After analyzing all 7 coins, provide a 2-sentence summary describing the overall market sentiment based on the list.\n\n"
            "**FORMATTING RULES (VERY IMPORTANT - FOLLOW EXACTLY):**\n"
            "1.  Start the entire response with the heading: `### Trending Market Analysis`\n"
            "2.  For each coin in Part 1, use a relevant emoji and **bold the coin name** (e.g., '🚀 **Bitcoin**').\n"
            "3.  Use bullet points (`* `) for the 3 analysis points under each coin.\n"
            "4.  Add **TWO blank lines** between each coin's analysis section.\n"
            "5.  Start Part 2 with the heading: `Overall Sentiment:`\n\n"
            "**FINAL CHECK:** Ensure absolutely NO profanity is present anywhere in the final output."
        )
        # --- END OF V7 PROMPT ---

        analysis = get_dobby_response(final_prompt)
        await update.message.reply_text(analysis, reply_markup=MAIN_MARKUP)

    except requests.exceptions.RequestException as e:
        print(f"CoinGecko API error: {e}")
        await update.message.reply_text("Sorry, I had trouble connecting to the CoinGecko API.")


# --- Conversation & Message Handler (V8 Prompt) ---
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
            f"🤖 Got it. Generating {quantity} complete thread(s) about '{context.user_data['topic']}' in a '{context.user_data['tone']}' tone...",
            reply_markup=MAIN_MARKUP
        )

        tone = context.user_data['tone']
        tone_description = ""
        # Tone descriptions remain the same
        if tone == "Shitposter":
            tone_description = "Witty, edgy, provocative, informal. Strong opinions. (Profanity like 'fuck' or 'shit' is allowed ONLY for this tone)."
        elif tone == "Conversational":
            tone_description = "Friendly, approachable, easy to read. **Absolutely NO profanity.**"
        elif tone == "Philosophical":
            tone_description = "Deep, abstract, thought-provoking. **Formal language. Absolutely NO profanity.**"
        elif tone == "Researcher":
            tone_description = "Data-driven, objective, analytical. **Formal language. Absolutely NO profanity.**"
        elif tone == "Trader":
            tone_description = "Action-oriented, concise, market-focused. **Professional tone. Absolutely NO profanity.**"

        # --- V8 PROMPT FOR THREAD GENERATION ---
        final_prompt = (
            "**IMPERATIVE RULE 1: FORBIDDEN WORDS:** Do NOT use profanity (e.g., 'fuck', 'shit', 'bitch', 'ass') UNLESS the requested tone is EXACTLY 'Shitposter'. For ALL OTHER TONES, your response MUST be 100% professional and contain ZERO profanity. Check your final output carefully.\n\n"
            "**IMPERATIVE RULE 2: COMPLETENESS:** You MUST generate the EXACT number of threads requested by the user ({context.user_data['quantity']}). Ensure each thread is fully written and does not cut off mid-sentence.\n\n"
            f"You are an expert content creator. Generate {context.user_data['quantity']} "
            f"ready-to-post Twitter threads about the topic: '{context.user_data['topic']}'.\n\n"
            f"**INSTRUCTIONS:**\n\n"
            f"1.  **TONE:** Write STRICTLY in this tone: **{tone_description}**\n\n"
            f"2.  **CONTENT:** Write full paragraphs for each tweet with deep insights. Do NOT use bullet points.\n\n"
            f"3.  **FORMATTING (FOLLOW EXACTLY):**\n"
            f"    - Each thread MUST have 6-8 tweets.\n"
            f"    - Separate each tweet (e.g., 1/8, 2/8) with ONE new line.\n"
            f"    - If generating >1 thread, separate them with '--- THREAD 2 ---', '--- THREAD 3 ---'.\n"
            f"    - Include relevant hashtags (#example) at the end of some tweets.\n\n"
            f"**FINAL CHECK:** Ensure Rule 1 (No Profanity Except Shitposter) and Rule 2 (Correct Quantity, No Cutoffs) are followed."

        )
        # --- END OF V8 PROMPT ---

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
    application.add_handler(CommandHandler("trending", trending)) # <-- Updated command

    # Register the main message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Your AI Content Strategist (V8 + V7) is now online!")
    application.run_polling()

if __name__ == '__main__':
    main()