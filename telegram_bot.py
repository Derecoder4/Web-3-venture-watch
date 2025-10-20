# telegram_bot.py
import os
from dotenv import load_dotenv
# --- CHANGES START HERE ---
from telegram import Update
# The new 'filters' is lowercase, and we build the application differently
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext
# --- CHANGES END HERE ---

# Import our Dobby function from the other file
from dobby_client import get_dobby_response

# Load the secret keys from the .env file
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# --- Command Handlers ---
# These functions define what the bot does when it receives a command.

async def start(update: Update, context: CallbackContext) -> None: # Functions are now async
    """Sends a welcome message when the /start command is issued."""
    welcome_text = (
        "Hi! I'm your AI Content Strategist, powered by Dobby.\n\n"
        "Give me a topic, and I'll generate X thread ideas for you.\n\n"
        "Try this: `/thread_ideas stablecoins in Africa`"
    )
    await update.message.reply_text(welcome_text) # Use 'await'

async def generate_ideas(update: Update, context: CallbackContext) -> None: # Functions are now async
    """Generates X thread ideas based on a user's topic."""
    try:
        topic = " ".join(context.args)
        if not topic:
            await update.message.reply_text("Please provide a topic after the command. \nExample: `/thread_ideas Web3 gaming`")
            return
    except (IndexError, ValueError):
        await update.message.reply_text("Please provide a topic. Example: `/thread_ideas Web3 gaming`")
        return

    await update.message.reply_text(f"🤖 Brainstorming ideas for '{topic}'... this might take a moment.")
    print(f"Received topic: {topic}")

    final_prompt = (
        "You are an expert X (Twitter) content strategist for a Web3 researcher. "
        f"Generate 3 distinct and engaging thread ideas about the topic: '{topic}'.\n\n"
        "For each idea, provide:\n"
        "1. A powerful, scroll-stopping hook (1-2 sentences).\n"
        "2. 3 to 4 bullet points that would be covered in the thread.\n"
        "3. A concluding thought or question to drive engagement."
    )
    
    response = get_dobby_response(final_prompt)
    
    await update.message.reply_text(response) # Use 'await'

# --- Main Bot Setup ---
def main() -> None:
    """Start the bot."""
    if not TELEGRAM_TOKEN:
        print("Error: TELEGRAM_TOKEN not found. Please set it in your .env file.")
        return

    # --- CHANGES START HERE ---
    # Create the Application and pass it your bot's token.
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Register the command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("thread_ideas", generate_ideas))
    
    # Run the bot until the user presses Ctrl-C
    print("Your AI Content Strategist is now online!")
    application.run_polling()
    # --- CHANGES END HERE ---

if __name__ == '__main__':
    main()