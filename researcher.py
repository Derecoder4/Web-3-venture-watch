# researcher.py
import requests
from bs4 import BeautifulSoup
from googlesearch import search

def get_text_from_url(url: str) -> str | None:
    """Fetches and cleans text content from a URL."""
    try:
        # Some sites block requests without a valid User-Agent
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()  # Check for HTTP errors

        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all paragraph tags, get their text, and join them
        paragraphs = soup.find_all('p')
        text = "\n".join([p.get_text() for p in paragraphs])

        # As a fallback if no <p> tags are found, get all text
        if not text:
            text = soup.get_text()
        
        # Clean up whitespace and limit to 4000 chars for the Dobby prompt
        clean_text = "\n".join([line for line in text.splitlines() if line.strip()])
        return clean_text[:4000]

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def research_topic(topic: str) -> str:
    """Searches a topic, scrapes the top result, and returns the content."""
    try:
        # Get the first 2 search results for the topic
        urls = [url for url in search(topic, num=2, stop=2, pause=1)]

        if not urls:
            return "Sorry, I couldn't find any good search results for that topic."

        # 1. Try to scrape the first URL
        content = get_text_from_url(urls[0])
        
        # 2. If the first fails (e.g., it's a PDF or protected), try the second
        if not content and len(urls) > 1:
            print(f"Scraping {urls[0]} failed, trying {urls[1]}")
            content = get_text_from_url(urls[1])

        if not content:
            return "Sorry, I found web pages but couldn't scrape their content."
        
        return content  # Return the raw, scraped text

    except Exception as e:
        print(f"Error in research_topic: {e}")
        return f"Sorry, an error occurred during research: {e}"