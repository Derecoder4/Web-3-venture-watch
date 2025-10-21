# researcher.py
from duckduckgo_search import DDGS

def research_topic(topic: str) -> str:
    """
    Searches a topic using DuckDuckGo and returns the
    scraped text from the top result.
    """
    print(f"Researcher: Searching for '{topic}'")
    try:
        # DDGS().text() searches and scrapes the content of the results
        # We ask for 2 results just in case the first one is bad.
        results = DDGS().text(topic, max_results=2)

        if not results:
            return "Sorry, I couldn't find any search results for that topic."

        # 'results' is a list of dictionaries. 'body' contains the scraped text.
        # We'll take the first result's text.
        content = results[0].get('body', None)

        # If the first result's body is empty, try the second
        if not content and len(results) > 1:
            print("First result empty, trying second...")
            content = results[1].get('body', None)

        if not content:
            return "Sorry, I found web pages but couldn't scrape their content."
        
        # Limit content to 4000 chars for the Dobby prompt
        return content[:4000]

    except Exception as e:
        print(f"Error in research_topic (duckduckgo_search): {e}")
        return f"Sorry, an error occurred during research: {e}"