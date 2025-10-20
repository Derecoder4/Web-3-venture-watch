# Content Bot

Quick setup instructions for this Telegram AI content bot.

Prerequisites
- Python 3.10+ installed and on PATH

Install dependencies (PowerShell):

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Quick import check (run in PowerShell):

```powershell
python check_env.py
```

Running the bot

1. Create a `.env` file with your Telegram token:

TELEGRAM_TOKEN=your_bot_token_here

2. Run:

```powershell
python telegram_bot.py
```

If Pylance in your editor still shows missing imports after installing packages, restart the editor or select the correct Python interpreter/virtual environment.
