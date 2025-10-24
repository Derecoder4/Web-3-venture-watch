# telegram_bot.py (V19 - Refiner Focus + Examples)
import os
import requests
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext

# Load the secret keys from the .env file FIRST
load_dotenv()

# --- Import Custom Modules ---
from dobby_client import get_dobby_response # Assuming dobby_client.py uses max_tokens=1024

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# --- Define Keyboards ---
MAIN_KEYBOARD = [
    ["✍️ Refine Draft", "🎨 Set Style"],
    ["❓ Help", "ℹ️ About"],
]
MAIN_MARKUP = ReplyKeyboardMarkup(MAIN_KEYBOARD, resize_keyboard=True)

REFINE_OPTIONS_KEYBOARD = [
    ["Make it Punchier 🥊", "Improve Clarity ✨"],
    ["Add Engagement Question❓", "Match My Style 🎨"],
    ["Suggest Hashtags #️⃣"],
    ["/cancel"],
]
REFINE_OPTIONS_MARKUP = ReplyKeyboardMarkup(REFINE_OPTIONS_KEYBOARD, resize_keyboard=True, one_time_keyboard=True)

# --- Utility Function for Sending Messages (Simple Split) ---
async def send_message(update: Update, context: CallbackContext, text: str, reply_markup=None):
    """Sends a message, splitting it simply by character limit if needed."""
    MAX_MESSAGE_LENGTH = 4096
    if not text: # Handle empty responses
        print("Warning: Attempted to send empty message.")
        await update.message.reply_text("Sorry, I couldn't generate a response for that.", reply_markup=reply_markup)
        return

    if len(text) <= MAX_MESSAGE_LENGTH:
        try:
            await update.message.reply_text(text, reply_markup=reply_markup)
        except Exception as e:
            print(f"Error sending single message part: {e}")
            await update.message.reply_text("Error: Could not send the response.", reply_markup=reply_markup)
    else:
        parts = [text[i : i + MAX_MESSAGE_LENGTH] for i in range(0, len(text), MAX_MESSAGE_LENGTH)]
        for i, part in enumerate(parts):
            final_markup = reply_markup if i == len(parts) - 1 else None
            try:
                await update.message.reply_text(part, reply_markup=final_markup)
            except Exception as e:
                print(f"Error sending message part {i+1}: {e}")
                # Try to inform user on the last part if possible
                if i == len(parts) - 1:
                     await update.message.reply_text("Error sending part of the message.", reply_markup=final_markup)


# --- Command Handlers ---
# (start, help_command, about, cancel, set_style_command, clear_style remain the same as V17)
async def start(update: Update, context: CallbackContext) -> None:
    context.user_data.clear()
    welcome_text = (
        "Hi! I'm your AI Content Assistant, powered by Dobby.\n\n"
        "Paste your draft tweet or tap '✍️ Refine Draft' to get started.\n\n"
        "Use `/setstyle` or '🎨 Set Style' to teach me your voice."
    )
    await send_message(update, context, welcome_text, reply_markup=MAIN_MARKUP)

async def help_command(update: Update, context: CallbackContext) -> None:
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

async def cancel(update: Update, context: CallbackContext) -> None:
    context.user_data.clear()
    await send_message(update, context,
        "Process cancelled. Paste a new draft or use the menu.",
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
        "✅ Style saved! Use the 'Match My Style' option during refinement.\n"
        "Use /clearstyle to remove it.",
        reply_markup=MAIN_MARKUP
    )

async def clear_style(update: Update, context: CallbackContext) -> None:
    if 'custom_style' in context.user_data:
        del context.user_data['custom_style']
        await send_message(update, context, "🗑️ Custom style cleared.", reply_markup=MAIN_MARKUP)
    else:
        await send_message(update, context, "No custom style was set.", reply_markup=MAIN_MARKUP)

# --- Refinement Conversation Logic ---
STATE_WAITING_DRAFT = 1
STATE_WAITING_REFINEMENT_CHOICE = 2

async def refine_command(update: Update, context: CallbackContext) -> None:
    await send_message(update, context, "Okay, please send me the draft text you want to refine.", reply_markup=ReplyKeyboardRemove())
    context.user_data['state'] = STATE_WAITING_DRAFT

# --- Main Message Handler ---
async def handle_message(update: Update, context: CallbackContext) -> None:
    text = update.message.text
    state = context.user_data.get('state')

    # --- 1. Handle Main Menu Buttons / Initial Input ---
    # (This section remains the same as V17)
    if not state:
        if text == "✍️ Refine Draft":
            await refine_command(update, context)
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

        context.user_data['draft_text'] = text
        await send_message(update, context, "Got the draft. How should I refine it?", reply_markup=REFINE_OPTIONS_MARKUP)
        context.user_data['state'] = STATE_WAITING_REFINEMENT_CHOICE
        return

    # --- 2. Handle Conversation States ---
    if state == STATE_WAITING_DRAFT:
         # (This section remains the same as V17)
        context.user_data['draft_text'] = text
        await send_message(update, context, "Okay, got the draft. How should I refine it?", reply_markup=REFINE_OPTIONS_MARKUP)
        context.user_data['state'] = STATE_WAITING_REFINEMENT_CHOICE
        return

    elif state == STATE_WAITING_REFINEMENT_CHOICE:
        refinement_choice = text
        draft_text = context.user_data.get('draft_text')

        if not draft_text:
            await send_message(update, context, "Error: Lost the draft text. Please start again.", reply_markup=MAIN_MARKUP)
            context.user_data.clear()
            return

        valid_choices = ["Make it Punchier 🥊", "Improve Clarity ✨", "Add Engagement Question❓", "Match My Style 🎨", "Suggest Hashtags #️⃣"]
        if refinement_choice not in valid_choices:
            await send_message(update, context, "Please choose a valid option from the buttons.", reply_markup=REFINE_OPTIONS_MARKUP)
            return

        thinking_message = await update.message.reply_text(f"🤖 Okay, refining using '{refinement_choice}'. Please wait...", reply_markup=MAIN_MARKUP)

        # --- Build the V19 Refinement Prompt ---
        prompt_instruction = ""
        custom_style = context.user_data.get('custom_style')
        output_example = "" # Variable for output examples

        # Define instructions and examples for each choice
        if refinement_choice == "Make it Punchier 🥊":
            prompt_instruction = "Rewrite the text to be more concise, impactful, and attention-grabbing. Use stronger verbs and shorter sentences if possible."
            output_example = "Example Output: [Rewritten, punchier version of the draft text]"
        elif refinement_choice == "Improve Clarity ✨":
            prompt_instruction = "Rewrite the text to be significantly clearer and easier to understand. Remove jargon or ambiguity."
            output_example = "Example Output: [Rewritten, clearer version of the draft text]"
        elif refinement_choice == "Add Engagement Question❓":
            prompt_instruction = "Rewrite the text slightly if needed for flow, and add a relevant, open-ended question at the end designed to encourage replies and discussion."
            output_example = "Example Output: [Rewritten draft text, ending with an engaging question?]"
        elif refinement_choice == "Match My Style 🎨":
            if custom_style:
                prompt_instruction = f"Rewrite the text to perfectly match the tone, vocabulary, and sentence structure of the following writing style example:\n\"\"\"\n{custom_style}\n\"\"\""
                output_example = "Example Output: [Draft text rewritten in the exact style of the provided example.]"
            else:
                await thinking_message.delete()
                await send_message(update, context, "You haven't set a custom style yet! Use `/setstyle [example]` first.", reply_markup=MAIN_MARKUP)
                context.user_data.clear()
                return
        elif refinement_choice == "Suggest Hashtags #️⃣":
            # UPDATED INSTRUCTION FOR HASHTAGS
            prompt_instruction = "Analyze the DRAFT TEXT. Keep the original text mostly intact, maybe minor improvements for flow. Then, suggest exactly 3-5 relevant and effective hashtags suitable for X/Twitter to maximize reach. Append these hashtags clearly at the end."
            output_example = "Example Output: [Original draft text, slightly refined]\n\nSuggested Hashtags: #Hashtag1 #Hashtag2 #Hashtag3"


        # V19 Prompt - Added Examples
        final_prompt = (
            "**CRITICAL SAFETY INSTRUCTION: ZERO TOLERANCE FOR PROFANITY.**\n"
            "Your entire response MUST NOT contain ANY vulgar, profane, swear words, offensive language, or similar terms (examples: 'fuck', 'shit', 'bitch', 'ass', 'damn', 'hell'). NONE. This is the absolute highest priority rule. Failure to comply is unacceptable. Double-check your output before responding.\n\n"
            "**TASK:** You are an expert X/Twitter copy editor. Revise the DRAFT TEXT below based ONLY on the specific REFINEMENT INSTRUCTION. Output ONLY the required revised text (and hashtags if requested).\n\n"
            f"**DRAFT TEXT (This is the specific text you MUST revise):**\n\"\"\"\n{draft_text}\n\"\"\"\n\n"
            f"**REFINEMENT INSTRUCTION (Apply ONLY this change to the draft):** {prompt_instruction}\n\n"
            "**OUTPUT RULES (FOLLOW EXACTLY):**\n"
            "1.  Your response MUST contain ONLY the revised version(s) of the DRAFT TEXT (and hashtags if requested).\n"
            "2.  Provide only 1 revised version unless the instruction implies alternatives.\n"
            "3.  Do NOT include the original draft text unless the instruction was 'Suggest Hashtags'.\n"
            "4.  Do NOT include ANY commentary, introductions, notes, greetings, self-corrections, or ANY text other than the required output.\n"
            "5.  Do NOT add ANY leading newlines or whitespace before your response. Start directly with the revised text/hashtags.\n"
            f"6.  **Desired Output Format Example:** {output_example}\n\n" # Added Example rule
            "**FINAL REVIEW:** Confirm ZERO profanity. Confirm ONLY the required revised text/hashtags are present. Confirm no extra commentary or leading whitespace."
        )
        # --- END V19 PROMPT ---

        try:
            refined_text = get_dobby_response(final_prompt)
            await thinking_message.delete()
            await send_message(update, context, refined_text, reply_markup=MAIN_MARKUP)

        except Exception as e:
            print(f"Error during AI call or processing: {e}")
            await thinking_message.delete()
            await send_message(update, context, "Sorry, an error occurred while generating the refinement.", reply_markup=MAIN_MARKUP)

        finally:
             context.user_data.clear()
        return

# --- Main Bot Setup ---
# (main function remains the same as V17)
def main() -> None:
    if not TELEGRAM_TOKEN:
        print("Error: TELEGRAM_TOKEN not found. Please set it in your .env file.")
        return

    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(CommandHandler("refine", refine_command))
    application.add_handler(CommandHandler("setstyle", set_style_command))
    application.add_handler(CommandHandler("clearstyle", clear_style))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Your AI Content Assistant (Refiner V19) is now online!")
    application.run_polling()

if __name__ == '__main__':
    main()