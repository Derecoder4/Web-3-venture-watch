# telegram_bot.py
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

# --- Conversation & Message Handler ---
async def handle_message(update: Update, context: CallbackContext) -> None:
    text = update.message.text
    state = context.user_data.get('state')

    # --- (Logic for main menu buttons and states AWAITING_TOPIC, AWAITING_TONE remains the same) ---
    if not state:
        # ... (same as previous version) ...
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

        context.user_data['topic'] = text
        custom_style = context.user_data.get('custom_style')
        if custom_style:
            await send_message(update, context, f"Using your custom style for '{text}'. How many threads (1-3)?", reply_markup=QUANTITY_MARKUP)
            context.user_data['state'] = 'AWAITING_QUANTITY'
        else:
            await send_message(update, context, "Got it. What tone should I use?", reply_markup=TONE_MARKUP)
            context.user_data['state'] = 'AWAITING_TONE'
        return

    if state == 'AWAITING_TOPIC':
        # ... (same as previous version) ...
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
        # ... (same as previous version) ...
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

        # --- Prompt Build Logic --- (Same V15 prompt structure)
        if custom_style:
            style_instruction = f"**STYLE GUIDE:** Mimic this style:\n\"\"\"\n{custom_style}\n\"\"\"\n"
            profanity_rule = "**ULTRA-STRICT RULE: Your response MUST NOT contain ANY vulgarity or profanity. Absolutely none.**\n\n"
        else: # No custom style
            tone_description = ""
            # ... (Keep all the elif blocks for tones and profanity rules the same as V15) ...
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

        # --- V15 PROMPT --- (Remains the same)
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
            f"    - Separate each tweet with ONE new line.\n"
            f"    - If generating >1 thread (and ONLY if requested quantity > 1), separate them with '--- THREAD 2 ---', '--- THREAD 3 ---'.\n"
            f"    - Include relevant hashtags (#example) at the end of some tweets.\n\n"
            f"**FINAL CHECK:** Ensure ZERO forbidden profanity (unless 'Shitposter'). Ensure EXACT quantity ({quantity}). Ensure EXACT length (8 tweets). Ensure correct formatting. Ensure ABSOLUTELY NO TEXT exists outside the requested thread(s)."
        )
        # --- END OF V15 PROMPT ---

        # --- Call API using the DEFAULT max_tokens (1024) ---
        response = get_dobby_response(final_prompt) # No max_tokens argument needed here

        # Use the send_message function to handle potential splitting
        await send_message(update, context, response, reply_markup=MAIN_MARKUP)

        context.user_data.clear()
        return

# --- Main Bot Setup --- (Remains the same, registers all commands including set/clearstyle)
def main() -> None:
    if not TELEGRAM_TOKEN:
        print("Error: TELEGRAM_TOKEN not found. Please set it in your .env file.")
        return

    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about))
    application.add_handler(CommandHandler("myideas", my_ideas))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(CommandHandler("generatethread", handle_message))
    # application.add_handler(CommandHandler("trending", trending)) # REMOVED
    application.add_handler(CommandHandler("setstyle", set_style))
    application.add_handler(CommandHandler("clearstyle", clear_style))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Your AI Content Strategist (V13 - Reduced Tokens) is now online!") # Updated version name
    application.run_polling()

if __name__ == '__main__':
    main()