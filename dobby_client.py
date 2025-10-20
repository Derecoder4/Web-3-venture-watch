# dobby_client.py
import os
import requests

# This is the correct API provider and endpoint
API_URL = "https://api.fireworks.ai/inference/v1/completions"

def get_dobby_response(prompt: str) -> str:
    """
    Sends a prompt to the Dobby model via the Fireworks AI API.
    """
    # This now gets the Fireworks API key from your .env file
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
        "max_tokens": 512,  # Controls the length of the response
        "temperature": 0.7, # Controls the creativity of the response
    }

    try:
        response = requests.post(API_URL, headers=headers, json=data)
        response.raise_for_status() 
        
        # Fireworks API returns the text in response['choices'][0]['text']
        response_data = response.json()
        return response_data['choices'][0]['text'].strip()
        
    except requests.exceptions.HTTPError as e:
        print(f"SERVER ERROR: {e.response.status_code} - {e.response.text}")
        return "Sorry, the server responded with an error. Check the terminal for details."
    except requests.exceptions.RequestException as e:
        print(f"CONNECTION ERROR: {e}")
        return "Sorry, I had trouble connecting to the Fireworks AI API."