import httpx
from mcp.server.fastmcp import FastMCP
from bs4 import BeautifulSoup
from typing import Dict, List
import urllib.parse
import wikipediaapi

# Create an MCP server
mcp = FastMCP("WikipediaFetcher")

# Create a global Wikipedia API session with descriptive user agent
wiki_session = wikipediaapi.Wikipedia(
    language="en",
    user_agent="WikiGameBot/1.0"  # Replace with your info
)

@mcp.tool()
async def get_wikipedia_page_text(page_title: str) -> Dict[str, str]:
    """
    Fetches the text content of a Wikipedia page using the Wikipedia API.
    
    Args:
        page_title: The title of the Wikipedia page to fetch
        
    Returns:
        A dictionary containing the page text or error message.
    """
    page = wiki_session.page(page_title)
    
    if page.exists():
        return {
            "text": page.text,
            "error": None
        }
    return {
        "text": "",
        "error": f"Page '{page_title}' not found"
    }

@mcp.tool() 
async def get_wikipedia_page_links_titles(page_title: str) -> Dict[str, List[str] | str]:
    """
    Fetches all links from a Wikipedia page using the Wikipedia API.
    
    Args:
        page_title: The title of the Wikipedia page to fetch links from
        
    Returns:
        A dictionary containing the list of linked page titles or error message.
    """
    page = wiki_session.page(page_title)
    
    if page.exists():
        links = [link for link in page.links.keys()]
        return {
            "links": links,
            "error": None
        }
    return {
        "links": [],
        "error": f"Page '{page_title}' not found"
    }

@mcp.tool()
async def get_wikipedia_page_links_urls(page_title: str) -> Dict[str, List[str] | str]:
    """
    Fetches all links from a Wikipedia page using the Wikipedia API.
    
    Args:
        page_title: The title of the Wikipedia page to fetch links from
        
    Returns:
        A dictionary containing the list of linked page URLs or error message.
    """
    page = wiki_session.page(page_title)
    
    if page.exists():
        links = [f"https://en.wikipedia.org/wiki/{link}" for link in page.links.keys()]
        return {
            "links": links,
            "error": None
        }
    return {
        "links": [],
        "error": f"Page '{page_title}' not found"
    }

if __name__ == "__main__":
    # This allows running the server directly using "python server.py"
    # For development, "mcp dev server.py" is usually preferred.
    mcp.run()