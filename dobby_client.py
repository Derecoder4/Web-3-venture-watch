# dobby_client.py
import os
import requests

# Get the API key from our .env file
SENTIENT_API_KEY = os.getenv("SENTIENT_API_KEY")
# IMPORTANT: Use the actual API URL provided by Sentient. This is a placeholder.
DOBBY_API_URL = "https://api.sentient.xyz/v1/models/dobby/query"

def get_dobby_response(prompt: str) -> str:
    """
    Sends a prompt to the Dobby API and gets a response.
    """
    if not SENTIENT_API_KEY:
        return "Error: SENTIENT_API_KEY is not set. Please check your .env file."

    headers = {
        "Authorization": f"Bearer {SENTIENT_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {"prompt": prompt}

    try:
        response = requests.post(DOBBY_API_URL, headers=headers, json=data)
        response.raise_for_status()
        
        # Adjust '.get("response")' based on the actual API output from Sentient's docs
        return response.json().get("response", "Sorry, I received an empty response.")
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return "Sorry, I had trouble connecting to the Dobby AI."