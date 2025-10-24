# telegram_bot.py (V13.1 - Refiner Focus)
import os
import requests
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext

# Load the secret keys from the .env file FIRST
load_dotenv()

# --- Import Custom Modules ---
from dobby_client import get_dobby_response

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# --- Define Keyboards ---
# --- UPDATED MAIN KEYBOARD ---
MAIN_KEYBOARD = [
    ["✍️ Refine Draft", "🎨 Set Style"],
    ["❓ Help", "ℹ️ About"],
]
MAIN_MARKUP = ReplyKeyboardMarkup(MAIN_KEYBOARD, resize_keyboard=True)
# --- END UPDATE ---

# (Tone and Quantity keyboards are no longer needed for refinement flow, but keep for now if setstyle uses tones)
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

# Refinement options keyboard
REFINE_OPTIONS_KEYBOARD = [
    ["Make it Punchier 🥊", "Improve Clarity ✨"],
    ["Add Engagement Question❓", "Match My Style 🎨"],
    ["Suggest Hashtags #️⃣"],
    ["/cancel"],
]
REFINE_OPTIONS_MARKUP = ReplyKeyboardMarkup(REFINE_OPTIONS_KEYBOARD, resize_keyboard=True, one_time_keyboard=True)


# --- Utility Function for Sending Messages ---
async def send_message(update: Update, context: CallbackContext, text: str, reply_markup=None):
    MAX_MESSAGE_LENGTH = 4096
    if len(text) <= MAX_MESSAGE_LENGTH:
        await update.message.reply_text(text, reply_markup=reply_markup)
    else:
        parts = [text[i : i + MAX_MESSAGE_LENGTH] for i in range(0, len(text), MAX_MESSAGE_LENGTH)]
        for i, part in enumerate(parts):
            final_markup = reply_markup if i == len(parts) - 1 else None
            await update.message.reply_text(part, reply_markup=final_markup)

# --- Command Handlers ---

async def start(update: Update, context: CallbackContext) -> None:
    context.user_data.clear()
    welcome_text = (
        "Hi! I'm your AI Content Assistant, powered by Dobby.\n\n"
        "Paste your draft tweet or tap '✍️ Refine Draft' to get started.\n\n"
        "Use `/setstyle` or '🎨 Set Style' to teach me your voice."
    )
    await send_message(update, context, welcome_text, reply_markup=MAIN_MARKUP)

async def help_command(update: Update, context: CallbackContext) -> None:
    # Updated help text for Refiner
    help_text = (
        "Here's how to use me:\n\n"
        "1.  **Paste your draft tweet:** I'll ask how you want to refine it.\n"
        "2.  **Tap '✍️ Refine Draft'**: I'll prompt you for the text.\n"
        "3.  **/setstyle [example]** or **'🎨 Set Style'**: Teach me your writing style.\n"
        "4.  **/clearstyle**: Reset to default style.\n"
        "5.  **/about**: Learn about this bot.\n"
        "6.  **/cancel**: Stop the current refinement."
    )
    await send_message(update, context, help_text, reply_markup=MAIN_MARKUP)

async def about(update: Update, context: CallbackContext) -> None:
    about_text = (
        "This is an AI Content Assistant bot by @joshehh for the Sentient Builder Program.\n\n"
        "It uses the **Dobby model** via Fireworks AI to help refine your X/Twitter content."
    )
    await send_message(update, context, about_text, reply_markup=MAIN_MARKUP)

# (my_ideas command is removed as it's not relevant to refiner)

async def cancel(update: Update, context: CallbackContext) -> None:
    context.user_data.clear()
    await send_message(update, context,
        "Process cancelled. Paste a new draft or use the menu.",
        reply_markup=MAIN_MARKUP
    )

async def set_style_command(update: Update, context: CallbackContext) -> None: # Renamed slightly
    """Handles the /setstyle command."""
    style_example = " ".join(context.args)
    if not style_example or len(style_example) < 10:
        await send_message(update, context,
            "Please provide example text after the command.\n"
            "Example: `/setstyle Your example tweet text here...`"
        )
        return

    context.user_data['custom_style'] = style_example
    await send_message(update, context,
        "✅ Style saved! Use the 'Match My Style' option during refinement.\n"
        "Use /clearstyle to remove it.",
        reply_markup=MAIN_MARKUP
    )

async def clear_style(update: Update, context: CallbackContext) -> None:
    if 'custom_style' in context.user_data:
        del context.user_data['custom_style']
        await send_message(update, context,
            "🗑️ Custom style cleared.",
            reply_markup=MAIN_MARKUP
        )
    else:
        await send_message(update, context,
            "No custom style was set.",
            reply_markup=MAIN_MARKUP
        )

# --- Refinement Conversation Logic ---

# Define states for the conversation
STATE_WAITING_DRAFT = 1
STATE_WAITING_REFINEMENT_CHOICE = 2

async def refine_command(update: Update, context: CallbackContext) -> None:
    """Starts the refinement process via command."""
    await send_message(update, context, "Okay, please send me the draft text you want to refine.", reply_markup=ReplyKeyboardRemove())
    context.user_data['state'] = STATE_WAITING_DRAFT

# --- Main Message Handler ---
async def handle_message(update: Update, context: CallbackContext) -> None:
    text = update.message.text
    state = context.user_data.get('state')

    # --- 1. Handle Main Menu Buttons / Initial Input ---
    if not state:
        # --- UPDATED BUTTON CHECKS ---
        if text == "✍️ Refine Draft":
            await refine_command(update, context) # Use the command function
            return
        elif text == "🎨 Set Style":
            await send_message(update, context, "Please send your style example using the command:\n`/setstyle [your example text]`", reply_markup=MAIN_MARKUP)
            return
        elif text == "❓ Help":
            await help_command(update, context)
            return
        elif text == "ℹ️ About":
            await about(update, context)
            return
        # --- END UPDATE ---

        # If no state and not a button, treat it as a draft to refine
        context.user_data['draft_text'] = text
        await send_message(update, context, "Got the draft. How should I refine it?", reply_markup=REFINE_OPTIONS_MARKUP)
        context.user_data['state'] = STATE_WAITING_REFINEMENT_CHOICE
        return

    # --- 2. Handle Conversation States ---
    if state == STATE_WAITING_DRAFT:
        context.user_data['draft_text'] = text
        await send_message(update, context, "Okay, got the draft. How should I refine it?", reply_markup=REFINE_OPTIONS_MARKUP)
        context.user_data['state'] = STATE_WAITING_REFINEMENT_CHOICE
        return

    elif state == STATE_WAITING_REFINEMENT_CHOICE:
        refinement_choice = text
        draft_text = context.user_data.get('draft_text')

        if not draft_text:
            await send_message(update, context, "Something went wrong, I lost the draft text. Please start again.", reply_markup=MAIN_MARKUP)
            context.user_data.clear()
            return

        # Check if valid choice
        valid_choices = ["Make it Punchier 🥊", "Improve Clarity ✨", "Add Engagement Question❓", "Match My Style 🎨", "Suggest Hashtags #️⃣"]
        if refinement_choice not in valid_choices:
            await send_message(update, context, "Please choose a valid refinement option from the buttons.", reply_markup=REFINE_OPTIONS_MARKUP)
            return

        await update.message.reply_text(f"🤖 Okay, refining your draft to '{refinement_choice}'. Please wait...", reply_markup=MAIN_MARKUP)

        # --- Build the Refinement Prompt ---
        prompt_instruction = ""
        custom_style = context.user_data.get('custom_style')

        if refinement_choice == "Make it Punchier 🥊":
            prompt_instruction = "Rewrite the text to be more concise, impactful, and attention-grabbing. Use stronger verbs and shorter sentences."
        elif refinement_choice == "Improve Clarity ✨":
            prompt_instruction = "Rewrite the text to be clearer, easier to understand, and remove any jargon or ambiguity."
        elif refinement_choice == "Add Engagement Question❓":
            prompt_instruction = "Rewrite the text and add a relevant, open-ended question at the end to encourage replies."
        elif refinement_choice == "Match My Style 🎨":
            if custom_style:
                prompt_instruction = f"Rewrite the text to perfectly match the following writing style:\n\"\"\"\n{custom_style}\n\"\"\""
            else:
                await send_message(update, context, "You haven't set a custom style yet! Use `/setstyle [example]` first.", reply_markup=MAIN_MARKUP)
                context.user_data.clear() # Clear state as the flow is broken
                return
        elif refinement_choice == "Suggest Hashtags #️⃣":
            prompt_instruction = "Analyze the text and suggest 3-5 relevant and effective hashtags to maximize reach."

        final_prompt = (
            "**TASK:** You are an expert X/Twitter copy editor. The user has provided draft text and a refinement instruction. Your goal is to provide 1-2 improved versions based ONLY on the instruction. Respond ONLY with the refined text.\n\n"
            "**DRAFT TEXT:**\n"
            f"\"\"\"\n{draft_text}\n\"\"\"\n\n"
            f"**REFINEMENT INSTRUCTION:** {prompt_instruction}\n\n"
            "**OUTPUT:**\n"
            "[Provide 1 or 2 refined versions of the draft text based on the instruction. Do not add any commentary before or after the refined text.]"
        )

        # Get response from Dobby (using default max_tokens)
        refined_text = get_dobby_response(final_prompt)

        await send_message(update, context, refined_text, reply_markup=MAIN_MARKUP)
        context.user_data.clear() # Clear state after successful refinement
        return

# --- Main Bot Setup ---
def main() -> None:
    if not TELEGRAM_TOKEN:
        print("Error: TELEGRAM_TOKEN not found. Please set it in your .env file.")
        return

    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about))
    # application.add_handler(CommandHandler("myideas", my_ideas)) # Removed
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(CommandHandler("refine", refine_command)) # New command to start
    # application.add_handler(CommandHandler("generatethread", handle_message)) # Removed
    application.add_handler(CommandHandler("setstyle", set_style_command)) # Use specific name
    application.add_handler(CommandHandler("clearstyle", clear_style))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Your AI Content Assistant (Refiner V1) is now online!")
    application.run_polling()

if __name__ == '__main__':
    main()