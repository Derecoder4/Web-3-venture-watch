# researcher.py
import requests
from bs4 import BeautifulSoup
from googlesearch import search

def get_text_from_url(url: str) -> str | None:
    """Fetches and cleans text content from a URL."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.find_all('p')
        text = "\n".join([p.get_text() for p in paragraphs])

        if not text:
            text = soup.get_text()
        
        clean_text = "\n".join([line for line in text.splitlines() if line.strip()])
        return clean_text[:4000]

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def research_topic(topic: str) -> str:
    """Searches a topic, scrapes the top result, and returns the content."""
    try:
        # --- THIS IS THE CORRECTED LINE ---
        # The correct argument is 'num_results'
        urls = [url for url in search(topic, num_results=2, pause=1)]

        if not urls:
            return "Sorry, I couldn't find any good search results for that topic."

        content = get_text_from_url(urls[0])
        
        if not content and len(urls) > 1:
            print(f"Scraping {urls[0]} failed, trying {urls[1]}")
            content = get_text_from_url(urls[1])

        if not content:
            return "Sorry, I found web pages but couldn't scrape their content."
        
        return content

    except Exception as e:
        print(f"Error in research_topic: {e}")
        return f"Sorry, an error occurred during research: {e}"