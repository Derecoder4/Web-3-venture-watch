# telegram_bot.py
import os
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext

# Load the secret keys from the .env file FIRST
load_dotenv()

# --- Import Custom Modules ---
# Import our Dobby function AFTER loading the .env
from dobby_client import get_dobby_response
# Import our new researcher function
from researcher import research_topic

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
    context.user_data.clear()  # Clear any old conversation state
    welcome_text = (
        "Hi! I'm your AI Content Strategist, powered by Dobby.\n\n"
        "Tap '💡 Generate New Idea' or send me a topic to get started.\n\n"
        "You can also use `/research [topic]` to get live info."
    )
    await update.message.reply_text(welcome_text, reply_markup=MAIN_MARKUP)

async def help_command(update: Update, context: CallbackContext) -> None:
    """Sends a helpful message."""
    help_text = (
        "Here's how to use me:\n\n"
        "1.  **Just send a topic:** I'll ask you for the tone and quantity.\n"
        "2.  **/research [topic]**: Get a real-time summary about any topic.\n"
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

async def research(update: Update, context: CallbackContext) -> None:
    """Researches a topic, scrapes content, and summarzies it with Dobby."""
    try:
        topic = " ".join(context.args)
        if not topic:
            await update.message.reply_text(
                "Please provide a topic. \nExample: `/research Kaito crypto project`"
            )
            return
    except (IndexError, ValueError):
        await update.message.reply_text("Please provide a topic.")
        return

    await update.message.reply_text(f"🔬 Researching '{topic}'... this might take a minute.")

    # 1. Get the scraped text from your new researcher.py
    scraped_text = research_topic(topic)

    # 2. Check if scraping failed
    if scraped_text.startswith("Sorry,"):
        await update.message.reply_text(scraped_text, reply_markup=MAIN_MARKUP)
        return
    
    # 3. Build the prompt for Dobby
    final_prompt = (
        "You are a research analyst. A user has provided you with raw, scraped text from a webpage. "
        "Your job is to read the text and provide a concise, factual summary.\n\n"
        f"**TOPIC:** {topic}\n\n"
        "**SCRAPED TEXT:**\n"
        f"\"\"\"\n{scraped_text}\n\"\"\"\n\n"
        "**YOUR TASK:**\n"
        "Based *only* on the text provided, write a clean, detailed summary of the topic. "
        "Do not add any information not present in the text."
    )

    # 4. Get the response from Dobby
    response = get_dobby_response(final_prompt)
    await update.message.reply_text(response, reply_markup=MAIN_MARKUP)

# --- Conversation & Message Handler ---

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
        
        # --- Build a smarter prompt ---
        
        # First, let's create better descriptions for each tone
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

        # Second, build the final prompt with new formatting rules
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

        # Get the response from Dobby
        response = get_dobby_response(final_prompt)
        await update.message.reply_text(response, reply_markup=MAIN_MARKUP)
        
        # Clear the state and end the conversation
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
    application.add_handler(CommandHandler("research", research)) # <-- New command
    
    # Register the main message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Your AI Content Strategist (V4) is now online!")
    application.run_polling()

if __name__ == '__main__':
    main()