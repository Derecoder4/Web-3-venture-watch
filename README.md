AI Content Strategist Bot for Telegram 🤖
A Telegram bot built for the Sentient Builder Program that acts as an AI-powered content assistant for creators, researchers, and builders in the Web3 and AI space.

This bot helps you overcome writer's block by generating structured and engaging X (formerly Twitter) thread ideas. By providing a simple topic, you'll receive multiple thread outlines, each complete with a powerful hook, key discussion points, and a question to drive engagement.


✨ Key Features
Generate Structured Ideas: Get complete thread outlines, not just loose concepts.

High-Quality Content: Outlines include a hook, key points, and a concluding thought.

AI-Powered: Utilizes Sentient's dobby-unhinged-llama-3-3-70b-new model to ensure creative and relevant content.

🛠️ Technology Stack
Language: Python

AI Model: Sentient's dobby-unhinged-llama-3-3-70b-new

API Provider: Fireworks AI

Telegram Framework: python-telegram-bot

🚀 Getting Started
Follow these instructions to get a copy of the project up and running on your local machine.

Prerequisites
Python 3.10+ installed

Git installed

Installation & Setup
Clone the repository:

Bash

git  https://github.com/Derecoder4/sentient-ai-content-bot.git
cd Doddy-framework-guide
Create and activate a virtual environment:

On Windows:

Bash

python -m venv venv
.\venv\Scripts\activate
On macOS & Linux:

Bash

python3 -m venv venv
source venv/bin/activate
Install the required dependencies:

Bash

pip install -r requirements.txt
Configure your environment variables:

Create a new file named .env in the root of the project.

Copy the contents of the example below into your new file.

Add your secret API keys to the file.

Your .env file should look like this:

# Get this from Telegram's @BotFather
TELEGRAM_TOKEN=123456:ABC-DEF1234567890

# Get this from your Fireworks AI account dashboard
FIREWORKS_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxx
Running the Bot
With your virtual environment active, run the following command in your terminal:

Bash

python telegram_bot.py
You should see the message: Your AI Content Strategist is now online!

Usage
Interact with the bot directly inside your Telegram app.

Start the bot:

/start
Generate thread ideas:

/thread_ideas [your topic here]
Example: /thread_ideas the future of decentralized identity
