# dobby_client.py
import os
import requests

# This is the correct API provider and endpoint
API_URL = "https://api.fireworks.ai/inference/v1/completions"

# dobby_client.py
# ... (imports and API_URL remain the same) ...

def get_dobby_response(prompt: str, max_tokens: int = 1024) -> str: # Add max_tokens argument with default
    """
    Sends a prompt to the Dobby model via the Fireworks AI API.
    """
    api_key = os.getenv("FIREWORKS_API_KEY")

    if not api_key:
        return "Error: FIREWORKS_API_KEY is not set. Please check your .env file."

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    data = {
        "model": "accounts/sentientfoundation/models/dobby-unhinged-llama-3-3-70b-new",
        "prompt": prompt,
        "max_tokens": max_tokens, # Use the passed-in value
        "temperature": 0.7,
    }

    try:
        response = requests.post(API_URL, headers=headers, json=data)
        response.raise_for_status()

        response_data = response.json()
        # Check if choices exist and have text
        choices = response_data.get('choices')
        if choices and len(choices) > 0 and 'text' in choices[0]:
             return choices[0]['text'].strip()
        else:
            print(f"Unexpected API response format: {response_data}")
            return "Sorry, I received an unexpected response format from the AI."

    except requests.exceptions.HTTPError as e:
        print(f"SERVER ERROR: {e.response.status_code} - {e.response.text}")
        # Try to parse the error detail if it's JSON
        try:
            error_detail = e.response.json().get('detail', e.response.text)
        except ValueError: # If response is not JSON
            error_detail = e.response.text
        return f"Sorry, the server responded with an error: {error_detail}"
    except requests.exceptions.RequestException as e:
        print(f"CONNECTION ERROR: {e}")
        return "Sorry, I had trouble connecting to the Fireworks AI API."
    except Exception as e: # Catch potential JSON parsing errors too
        print(f"Error parsing response or other exception: {e}")
        return "Sorry, an unexpected error occurred while processing the AI response."