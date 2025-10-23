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
        "Use `/trending` for market info, or `/setstyle` to teach me your voice."
    )
    await update.message.reply_text(welcome_text, reply_markup=MAIN_MARKUP)

async def help_command(update: Update, context: CallbackContext) -> None:
    help_text = (
        "Here's how to use me:\n\n"
        "1.  **Just send a topic:** I'll ask for tone & quantity (or use your custom style).\n"
        "2.  **/trending**: Get AI analysis on CoinGecko's top 7.\n"
        "3.  **/setstyle [example]**: Teach me your writing style.\n"
        "4.  **/clearstyle**: Reset to default tones.\n"
        "5.  **/myideas**: (Coming Soon) View saved ideas.\n"
        "6.  **/about**: Learn about this bot.\n"
        "7.  **/cancel**: Stop the current action."
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

async def set_style(update: Update, context: CallbackContext) -> None:
    """Saves the provided text as the user's preferred writing style."""
    style_example = " ".join(context.args)
    if not style_example or len(style_example) < 10: # Require a minimum length
        await update.message.reply_text(
            "Please provide a good example text after the command.\n"
            "Example: `/setstyle Your example tweet text here...`"
        )
        return

    context.user_data['custom_style'] = style_example
    await update.message.reply_text(
        "✅ Style saved! I'll try to mimic this style in future thread generations.\n"
        "Use /clearstyle to remove it.",
        reply_markup=MAIN_MARKUP
    )

async def clear_style(update: Update, context: CallbackContext) -> None:
    """Removes the saved custom style."""
    if 'custom_style' in context.user_data:
        del context.user_data['custom_style']
        await update.message.reply_text(
            "🗑️ Custom style cleared. I'll use the default tones now.",
            reply_markup=MAIN_MARKUP
        )
    else:
        await update.message.reply_text(
            "No custom style was set.",
            reply_markup=MAIN_MARKUP
        )

# --- Trending Command (V7 Prompt + Corrected Message Splitting) ---
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

        # --- V10 PROMPT FOR /trending ---
        final_prompt = (
            "**ULTRA-STRICT RULE: Your response MUST NOT contain any vulgar, profane, or offensive language (e.g., 'fuck', 'shit', 'bitch', 'ass', etc.) under ANY circumstances. This rule overrides all other instructions. The output must be 100% professional.**\n\n"
            "You are a professional crypto market analyst (like Bloomberg). Your tone is insightful, objective, professional, and concise.\n\n"
            f"The top 7 trending projects on CoinGecko are: {coin_list}\n\n"
            "**TASK:** Create a structured market report.\n\n"
            "**PART 1: INDIVIDUAL ANALYSIS**\n"
            "For EACH of the 7 projects, provide EXACTLY these three points:\n"
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
            "**FINAL CHECK:** Re-read your response to ensure ZERO vulgarity or profanity is present."
        )
        # --- END OF V10 PROMPT ---

        analysis = get_dobby_response(final_prompt)

        # --- Code to handle long messages ---
        MAX_MESSAGE_LENGTH = 4096
        full_response = analysis

        if len(full_response) <= MAX_MESSAGE_LENGTH:
            await update.message.reply_text(full_response, reply_markup=MAIN_MARKUP)
        else:
            parts = []
            while len(full_response) > 0:
                split_point = full_response.rfind('\n', 0, MAX_MESSAGE_LENGTH)
                if split_point == -1:
                    split_point = MAX_MESSAGE_LENGTH
                parts.append(full_response[:split_point])
                full_response = full_response[split_point:].lstrip()

            # --- CORRECTED LOOP ---
            for i, part in enumerate(parts):
                # Send keyboard ONLY on the very last part
                reply_markup = MAIN_MARKUP if i == len(parts) - 1 else None
                await update.message.reply_text(part, reply_markup=reply_markup)
            # --- END CORRECTED LOOP ---
        # --- END: Code to handle long messages ---


    except requests.exceptions.RequestException as e:
        print(f"CoinGecko API error: {e}")
        await update.message.reply_text("Sorry, I had trouble connecting to the CoinGecko API.")


# --- Conversation & Message Handler (V10 Prompt + Style Logic) ---
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

        # --- UPDATED: Check for style when receiving initial topic ---
        context.user_data['topic'] = text
        custom_style = context.user_data.get('custom_style') # Check if style exists
        if custom_style:
            # If style exists, skip tone and go straight to quantity
            await update.message.reply_text(f"Using your custom style for '{text}'. How many threads (1-3)?", reply_markup=QUANTITY_MARKUP)
            context.user_data['state'] = 'AWAITING_QUANTITY'
        else:
            # If no style, ask for tone as usual
            await update.message.reply_text("Got it. What tone should I use?", reply_markup=TONE_MARKUP)
            context.user_data['state'] = 'AWAITING_TONE'
        return
        # --- END UPDATE ---

    # --- 2. Handle Conversation States ---
    if state == 'AWAITING_TOPIC':
        # --- UPDATED: Check for style after getting topic via button ---
        context.user_data['topic'] = text
        custom_style = context.user_data.get('custom_style') # Check if style exists
        if custom_style:
            # If style exists, skip tone and go straight to quantity
            await update.message.reply_text(f"Using your custom style for '{text}'. How many threads (1-3)?", reply_markup=QUANTITY_MARKUP)
            context.user_data['state'] = 'AWAITING_QUANTITY'
        else:
            # If no style, ask for tone as usual
            await update.message.reply_text("Perfect. Now, what tone should I use?", reply_markup=TONE_MARKUP)
            context.user_data['state'] = 'AWAITING_TONE'
        return
        # --- END UPDATE ---

    elif state == 'AWAITING_TONE':
        # This state is now skipped if custom_style exists
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
        # Use tone in the confirmation message ONLY if custom_style is NOT set
        tone_or_style = f"'{context.user_data.get('tone', 'default')}' tone"
        if context.user_data.get('custom_style'):
            tone_or_style = "your custom style"

        await update.message.reply_text(
            f"🤖 Got it. Generating {quantity} complete thread(s) about '{context.user_data['topic']}' using {tone_or_style}...",
            reply_markup=MAIN_MARKUP
        )

        # --- V10 Prompt Build Logic ---
        tone = context.user_data.get('tone') # Use .get() in case it was skipped
        custom_style = context.user_data.get('custom_style')

        if custom_style:
            style_instruction = (
                f"**STYLE GUIDE (MOST IMPORTANT):** You MUST mimic the writing style found in this example:\n"
                f"\"\"\"\n{custom_style}\n\"\"\"\n\n"
                f"Pay close attention to vocabulary, sentence structure, and overall voice."
            )
            profanity_rule = "**ULTRA-STRICT RULE: Your response MUST NOT contain any vulgar, profane, or offensive language (e.g., 'fuck', 'shit', 'bitch', 'ass', etc.) under ANY circumstances. The output must be 100% professional.**\n\n"

        else: # No custom style, use selected tone
            tone_description = ""
            if tone == "Shitposter":
                tone_description = "Witty, edgy, provocative, informal. Strong opinions. (Profanity like 'fuck' or 'shit' is allowed ONLY for this tone)."
                profanity_rule = "**RULE: Profanity (e.g., 'fuck', 'shit') is allowed ONLY because the selected tone is 'Shitposter'.**\n\n"
            # (Keep the elif blocks for Conversational, Philosophical, Researcher, Trader as before, ensuring they set the ULTRA-STRICT profanity_rule)
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


        final_prompt = (
            f"{profanity_rule}"
            "**IMPERATIVE RULE 2: COMPLETENESS:** You MUST generate the EXACT number of threads requested ({context.user_data['quantity']}). Ensure each thread is fully written and does not cut off mid-sentence.\n\n"
            f"You are an expert content creator. Generate {context.user_data['quantity']} "
            f"ready-to-post Twitter threads about the topic: '{context.user_data['topic']}'.\n\n"
            f"**INSTRUCTIONS:**\n\n"
            f"1.  {style_instruction}\n\n"
            f"2.  **CONTENT:** Write full paragraphs for each tweet with deep insights. Do NOT use bullet points.\n\n"
            f"3.  **FORMATTING (FOLLOW EXACTLY):**\n"
            f"    - Each thread MUST have 6-8 tweets.\n"
            f"    - Separate each tweet (e.g., 1/8) with ONE new line.\n"
            f"    - If generating >1 thread, separate them with '--- THREAD 2 ---', etc.\n"
            f"    - Include relevant hashtags (#example) at the end of some tweets.\n\n"
            f"**FINAL CHECK:** Re-read your response to ensure NO forbidden profanity is present (unless 'Shitposter' tone was selected OR the custom style clearly implies it - default to NO profanity for custom styles) and that the correct number of complete threads were generated."
        )
        # --- END OF V10 PROMPT ---

        response = get_dobby_response(final_prompt)

        # --- Code to handle long messages ---
        MAX_MESSAGE_LENGTH = 4096
        full_response = response

        if len(full_response) <= MAX_MESSAGE_LENGTH:
            await update.message.reply_text(full_response, reply_markup=MAIN_MARKUP)
        else:
            parts = []
            while len(full_response) > 0:
                split_point = full_response.rfind('\n', 0, MAX_MESSAGE_LENGTH)
                if split_point == -1:
                    split_point = MAX_MESSAGE_LENGTH
                parts.append(full_response[:split_point])
                full_response = full_response[split_point:].lstrip()

            # --- CORRECTED LOOP ---
            for i, part in enumerate(parts):
                # Send keyboard ONLY on the very last part
                reply_markup = MAIN_MARKUP if i == len(parts) - 1 else None
                await update.message.reply_text(part, reply_markup=reply_markup)
            # --- END CORRECTED LOOP ---
        # --- END: Code to handle long messages ---

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
    application.add_handler(CommandHandler("trending", trending))
    application.add_handler(CommandHandler("setstyle", set_style))
    application.add_handler(CommandHandler("clearstyle", clear_style))

    # Register the main message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Your AI Content Strategist (V11) is now online!")
    application.run_polling()

if __name__ == '__main__':
    main()