
from duckduckgo_search import DDGS

def web_search(query: str, max_results: int = 5) -> str:
    """Performs a web search and returns a formatted string of results."""
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append(f"Title: {r['title']}\nSnippet: {r['body']}\nSource: {r['href']}\n")
        
        if not results:
            return "No web results found."
            
        return "\n---\n".join(results)
    except Exception as e:
        return f"Web Search Error: {str(e)}"

if __name__ == "__main__":
    # Test search
    print(web_search("Taremwa Studios itch.io"))
