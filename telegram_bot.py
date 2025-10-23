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

# --- Utility Function for Sending Messages (Handles Splitting) ---
async def send_message(update: Update, context: CallbackContext, text: str, reply_markup=None):
    """Sends a message, splitting it if it exceeds Telegram's limit."""
    MAX_MESSAGE_LENGTH = 4096
    if len(text) <= MAX_MESSAGE_LENGTH:
        await update.message.reply_text(text, reply_markup=reply_markup)
    else:
        parts = []
        # Simple split by character limit
        for i in range(0, len(text), MAX_MESSAGE_LENGTH):
            parts.append(text[i : i + MAX_MESSAGE_LENGTH])

        for i, part in enumerate(parts):
            final_markup = reply_markup if i == len(parts) - 1 else None
            await update.message.reply_text(part, reply_markup=final_markup)

# --- Command Handlers ---

async def start(update: Update, context: CallbackContext) -> None:
    context.user_data.clear()
    welcome_text = (
        "Hi! I'm your AI Content Strategist, powered by Dobby.\n\n"
        "Tap '💡 Generate New Idea' or send me a topic to get started.\n\n"
        "Use `/setstyle` to teach me your voice."
    )
    await send_message(update, context, welcome_text, reply_markup=MAIN_MARKUP)

async def help_command(update: Update, context: CallbackContext) -> None:
    # Updated help text (removed /trending)
    help_text = (
        "Here's how to use me:\n\n"
        "1.  **Just send a topic:** I'll ask for tone & quantity (or use your custom style).\n"
        "2.  **/setstyle [example]**: Teach me your writing style.\n"
        "3.  **/clearstyle**: Reset to default tones.\n"
        "4.  **/myideas**: (Coming Soon) View saved ideas.\n"
        "5.  **/about**: Learn about this bot.\n"
        "6.  **/cancel**: Stop the current action.\n"
        "7.  **/generatethread**: (Legacy) Starts the guided process."
    )
    await send_message(update, context, help_text, reply_markup=MAIN_MARKUP)

async def about(update: Update, context: CallbackContext) -> None:
    about_text = (
        "This is an AI bot built by @josh_ehh for the Sentient Builder Program.\n\n"
        "It uses the **Dobby model** via the Fireworks AI API to help you brainstorm content ideas."
    )
    await send_message(update, context, about_text, reply_markup=MAIN_MARKUP)

async def my_ideas(update: Update, context: CallbackContext) -> None:
    await send_message(update, context,
        "This feature is coming soon! This will allow you to save and view your best-generated ideas.",
        reply_markup=MAIN_MARKUP
    )

async def cancel(update: Update, context: CallbackContext) -> None:
    context.user_data.clear()
    await send_message(update, context,
        "Process cancelled. What's next?",
        reply_markup=MAIN_MARKUP
    )

async def set_style(update: Update, context: CallbackContext) -> None:
    style_example = " ".join(context.args)
    if not style_example or len(style_example) < 10:
        await send_message(update, context,
            "Please provide a good example text after the command.\n"
            "Example: `/setstyle Your example tweet text here...`"
        )
        return

    context.user_data['custom_style'] = style_example
    await send_message(update, context,
        "✅ Style saved! I'll try to mimic this style in future thread generations.\n"
        "Use /clearstyle to remove it.",
        reply_markup=MAIN_MARKUP
    )

async def clear_style(update: Update, context: CallbackContext) -> None:
    if 'custom_style' in context.user_data:
        del context.user_data['custom_style']
        await send_message(update, context,
            "🗑️ Custom style cleared. I'll use the default tones now.",
            reply_markup=MAIN_MARKUP
        )
    else:
        await send_message(update, context,
            "No custom style was set.",
            reply_markup=MAIN_MARKUP
        )


# --- Conversation & Message Handler (V12 Prompt + Style Logic) ---
async def handle_message(update: Update, context: CallbackContext) -> None:
    text = update.message.text
    state = context.user_data.get('state')

    # --- 1. Handle Main Menu Buttons ---
    if not state:
        if text == "💡 Generate New Idea":
            await send_message(update, context, "Great! What's the topic?", reply_markup=ReplyKeyboardRemove())
            context.user_data['state'] = 'AWAITING_TOPIC'
            return
        elif text == "📂 My Saved Ideas":
            await my_ideas(update, context)
            return
        elif text == "ℹ️ About":
            await about(update, context)
            return

        # Check for style when receiving initial topic
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
        # Check for style after getting topic via button
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
        tone_or_style = f"'{context.user_data.get('tone', 'default')}' tone"
        if context.user_data.get('custom_style'):
            tone_or_style = "your custom style"
        # Use simpler reply_text for this intermediate message
        await update.message.reply_text(
            f"🤖 Got it. Generating {quantity} complete thread(s) about '{context.user_data['topic']}' using {tone_or_style}...",
            reply_markup=MAIN_MARKUP
        )

        tone = context.user_data.get('tone')
        custom_style = context.user_data.get('custom_style')

        if custom_style:
            style_instruction = f"**STYLE GUIDE:** Mimic this style:\n\"\"\"\n{custom_style}\n\"\"\"\n"
            profanity_rule = "**ULTRA-STRICT RULE: Your response MUST NOT contain ANY vulgarity or profanity. Absolutely none.**\n\n"
        else:
            tone_description = ""
            if tone == "Shitposter":
                tone_description = "Witty, edgy, provocative, informal. Strong opinions. (Profanity allowed ONLY for this tone)."
                profanity_rule = "**RULE: Profanity is allowed ONLY because the selected tone is 'Shitposter'.**\n\n"
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

        # --- V12 PROMPT FOR THREAD GENERATION ---
        final_prompt = (
            f"{profanity_rule}"
            "**IMPERATIVE RULE 2: COMPLETENESS:** Generate the EXACT number of threads requested ({context.user_data['quantity']}). Ensure each thread is fully written and does not cut off.\n\n"
            f"You are an expert content creator. Generate {context.user_data['quantity']} "
            f"ready-to-post Twitter threads about the topic: '{context.user_data['topic']}'.\n\n"
            f"**INSTRUCTIONS:**\n"
            f"1.  {style_instruction}\n"
            f"2.  **CONTENT:** Write full paragraphs for each tweet with deep insights. Do NOT use bullet points.\n"
            f"3.  **FORMATTING (MUST FOLLOW EXACTLY):**\n"
            f"    - Each thread MUST have 6-8 tweets.\n"
            f"    - Separate each tweet (e.g., 1/8) with ONE new line.\n"
            f"    - If generating >1 thread, separate them with '--- THREAD 2 ---', etc.\n"
            f"    - Include relevant hashtags (#example) at the end of some tweets.\n\n"
            f"**FINAL CHECK:** Re-read response. Ensure ZERO forbidden profanity (unless 'Shitposter' tone). Ensure correct quantity ({context.user_data['quantity']}) and completeness."
        )
        # --- END OF V12 PROMPT ---

        response = get_dobby_response(final_prompt)
        # Use the new send_message function to handle potential splitting
        await send_message(update, context, response, reply_markup=MAIN_MARKUP)

        context.user_data.clear()
        return

# --- Main Bot Setup ---
def main() -> None:
    if not TELEGRAM_TOKEN:
        print("Error: TELEGRAM_TOKEN not found. Please set it in your .env file.")
        return

    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Register handlers (Removed /trending)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about))
    application.add_handler(CommandHandler("myideas", my_ideas))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(CommandHandler("generatethread", handle_message))
    # application.add_handler(CommandHandler("trending", trending)) # <-- REMOVED
    application.add_handler(CommandHandler("setstyle", set_style))
    application.add_handler(CommandHandler("clearstyle", clear_style))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Your AI Content Strategist (V13 - Focused) is now online!")
    application.run_polling()

if __name__ == '__main__':
    main()