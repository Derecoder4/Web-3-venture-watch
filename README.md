Crypto Startup Pulse Bot 🚀
A Telegram bot built for the Sentient Builder Program that acts as your AI analyst for the crypto startup scene. It monitors various crypto and tech news RSS feeds and uses Sentient's Dobby model (via Fireworks AI) to provide summarized digests of recent developments.

✨ Capabilities
News Aggregation: Fetches recent news articles from multiple RSS feeds (Cointelegraph, Decrypt, TechCrunch, etc.).

AI Summarization: Uses the Dobby LLM to read article snippets and generate concise, bulleted summaries focused on crypto startups.

Categorized Digests: Provides summaries tailored to specific areas:

General crypto startup news (/latest)

Funding rounds (/funding - uses TechCrunch, AI filters for crypto)

DeFi startups (/defi)

Web3 Gaming startups (/web3gaming)

Profanity Filtering: Includes a basic Python filter to reduce (but not eliminate) profanity from the AI's output.

🛠️ Setup (Local Development)
Follow these steps to run the bot on your own machine.

Prerequisites
Python 3.10+ installed.

Git installed.

Installation
Clone the repository:

Bash

git https://github.com/Derecoder4/Web-3-venture-watch.git
cd Web-3-venture-watch
Create and activate a virtual environment:

On Windows:

Bash

python -m venv venv
.\venv\Scripts\activate
On macOS & Linux:

Bash

python3 -m venv venv
source venv/bin/activate
(You should see (venv) in your terminal prompt).

Install dependencies:

Bash

pip install -r requirements.txt
Configure environment variables:

Create a file named .env in the project root.

Add your secret keys:

Code snippet

# Get from Telegram @BotFather
TELEGRAM_TOKEN=YOUR_TELEGRAM_BOT_TOKEN

# Get from Fireworks AI dashboard
FIREWORKS_API_KEY=YOUR_FIREWORKS_AI_KEY
Running the Bot
With your virtual environment active, run:

Bash

python telegram_bot.py
You should see the message: Your Crypto Startup Pulse Bot (...) is now online!

🚀 How to Use
Interact with the bot in your Telegram chat:

/start: Initializes the bot and shows the main keyboard.

/latest: Get a summary of recent general crypto startup news.

/funding: Get a summary of recent funding rounds (pulls from TechCrunch, AI attempts to filter for crypto).

/defi: Get a summary of recent news about DeFi startups.

/web3gaming: Get a summary of recent news about Web3 Gaming startups.

/help: Shows the list of commands.

/about: Displays information about the bot.

You can also use the persistent keyboard buttons as shortcuts for the main commands.

⚠️ Limitations
Dobby Model Personality: The underlying Dobby model is designed to be "blunt, a bit rude, and often controversial." While prompts and filters attempt to enforce professionalism, occasional profanity or unwanted commentary may still leak through, especially in complex summarization tasks.

RSS Feed Dependency: The quality and relevance of the news digests depend entirely on the content available in the configured RSS feeds. The /funding command relies on the general TechCrunch feed, so its crypto relevance may vary. Feed URLs might break or change over time.

Summarization Accuracy: LLM summaries might occasionally miss nuances, hallucinate details not present in the source text, or misinterpret complex information. The bot attempts to mitigate this by instructing Dobby to use only the provided snippets.

No Memory/Refinement: The bot processes each command independently and doesn't remember past conversations or allow for refining the generated summaries.
