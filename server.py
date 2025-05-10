import httpx
from mcp.server.fastmcp import FastMCP
from bs4 import BeautifulSoup
from typing import Dict, List
import urllib.parse

# Create an MCP server
mcp = FastMCP("WikipediaFetcher")


@mcp.tool()
async def fetch_wikipedia_page(page_title: str) -> Dict[str, str | List[str]]:
    """
    Fetches the main text content and internal links of a Wikipedia page.

    Args:
        page_title: The title of the Wikipedia page (e.g., "Python (programming language)").

    Returns:
        A dictionary containing:
            "main_text": The main article text.
            "wikipedia_links": A list of full URLs to other Wikipedia articles.
        Or an error message if fetching/parsing fails.
    """
    formatted_title = page_title.replace(" ", "_")
    base_url = "https://en.wikipedia.org"
    url = f"{base_url}/wiki/{formatted_title}"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract main content text
            # Wikipedia's main content is usually within div#mw-content-text -> div.mw-parser-output
            content_div = soup.find('div', id='mw-content-text')
            main_text_content = ""
            if content_div:
                parser_output_div = content_div.find('div', class_='mw-parser-output')
                if parser_output_div:
                    # Remove tables, navboxes, and other non-prose elements for cleaner text
                    for el_to_remove in parser_output_div.find_all(['table', 'div.navbox', 'div.thumb', 'div.hatnote', 'div.reflist', 'div.catlinks']):
                        el_to_remove.decompose()
                    main_text_content = parser_output_div.get_text(separator='\\n', strip=True)
                else:
                    main_text_content = "Could not find mw-parser-output div." # Fallback if structure is unexpected
            else:
                main_text_content = "Could not find mw-content-text div." # Fallback

            # Extract internal Wikipedia links from the main content area
            wikipedia_links = []
            if content_div: # Search within the same content_div for consistency
                parser_output_div_for_links = content_div.find('div', class_='mw-parser-output') # Re-find or use the one from above
                if parser_output_div_for_links:
                    for a_tag in parser_output_div_for_links.find_all('a', href=True):
                        href = a_tag['href']
                        if href.startswith('/wiki/') and ':' not in href:
                            # Filter out common non-article links like Main_Page or special pages
                            if not href.startswith(('/wiki/Main_Page', '/wiki/Special:', '/wiki/Help:', '/wiki/Category:', '/wiki/Portal:', '/wiki/Template:', '/wiki/Wikipedia:')):
                                wikipedia_links.append(f"{base_url}{href}")
            
            return {
                "main_text": main_text_content,
                "wikipedia_links": list(set(wikipedia_links)) # Remove duplicates
            }
            
    except httpx.HTTPStatusError as e:
        return {
            "error": f"Error fetching page '{page_title}': HTTP {e.response.status_code} - {e.response.reason_phrase}",
            "main_text": "",
            "wikipedia_links": []
        }
    except httpx.RequestError as e:
        return {
            "error": f"Error fetching page '{page_title}': {str(e)}",
            "main_text": "",
            "wikipedia_links": []
        }
    except Exception as e:
        return {
            "error": f"An unexpected error occurred while fetching page '{page_title}': {str(e)}",
            "main_text": "",
            "wikipedia_links": []
        }

@mcp.tool()
async def fetch_next_wikipedia_page(page_title: str) -> str:
    """
    Fetches and processes a Wikipedia page for the 'Wikipedia race game'.
    Returns HTML content with only internal Wikipedia article links active.
    References, external links, and non-essential elements are removed or de-linked.
    Infoboxes (sidebars) are preserved.

    Args:
        page_title: The title of the Wikipedia page.

    Returns:
        An HTML string of the processed page content, or an error message.
    """
    formatted_title = page_title.replace(" ", "_")
    base_url = "https://en.wikipedia.org"
    url = f"{base_url}/wiki/{formatted_title}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            content_div = soup.find('div', id='mw-content-text')
            if not content_div:
                return "Error: Could not find main content div ('mw-content-text')."
            
            parser_output_div = content_div.find('div', class_='mw-parser-output')
            if not parser_output_div:
                return "Error: Could not find parser output div ('mw-parser-output') within main content."

            # 1. Decompose unwanted elements
            elements_to_remove_selectors = [
                'sup.reference',         # Reference superscripts [1], [2]
                'div.reflist',           # Reference list section
                'div.catlinks',          # Category links at the bottom
                'div.navbox',            # Navigation boxes
                'div.thumb',             # Thumbnails in text, infobox images are usually in tables
                'div.hatnote',           # Disambiguation notes at the top
                '#siteSub',              # "From Wikipedia, the free encyclopedia"
                '#jump-to-nav',          # "Jump to navigation" link
                '.mw-editsection',       # "[edit]" links
                '.mw-kartographer-maplink', # Interactive map links
                '#toc'                   # Table of Contents - can be noisy for the game.
            ]
            for selector_text in elements_to_remove_selectors:
                for el in parser_output_div.select(selector_text):
                    el.decompose()
            
            # Remove tables that are NOT infoboxes
            # Infoboxes often have class 'infobox' or are 'vcard' tables.
            for table in parser_output_div.find_all('table'):
                table_classes = table.get('class', [])
                if not any(cls in ['infobox', 'vcard', 'metadata'] for cls in table_classes): # Keep metadata tables too (like authority control)
                    # Check if it's a simple data table or something we want to keep.
                    # This is a heuristic; might need refinement for specific table types.
                    # For now, if not clearly an infobox or metadata, remove it to simplify.
                    is_likely_infobox_style = any(style_attr in table.get('style', '').lower() for style_attr in ['float:right', 'float:left', 'margin:0.5em 0 0.5em 1em'])
                    if not is_likely_infobox_style and 'infobox' not in str(table).lower(): # another check
                         table.decompose()


            # 2. Process links
            allowed_link_prefixes = ('/wiki/File:', '/wiki/Image:') # To keep image links in infoboxes working if they go to a description page

            for a_tag in parser_output_div.find_all('a', href=True):
                href = a_tag['href']
                
                is_internal_article_link = (
                    href.startswith('/wiki/') and 
                    ':' not in href.split('/wiki/')[1].split('#')[0].split('?')[0] and # Check no colon in the actual page title part
                    not href.startswith((
                        '/wiki/Main_Page', '/wiki/Special:', '/wiki/Help:', '/wiki/Category:', 
                        '/wiki/Portal:', '/wiki/Template:', '/wiki/Wikipedia:', '/wiki/Talk:'
                    ))
                )
                is_allowed_file_link = href.startswith(allowed_link_prefixes)


                if is_internal_article_link:
                    a_tag['href'] = f"{base_url}{href.split('#')[0]}" # Make absolute and remove fragment
                    # Optionally, add target="_blank" if this HTML is rendered directly by a browser
                    # a_tag['target'] = '_blank' 
                elif is_allowed_file_link: # Keep links to File/Image pages if they are in infoboxes etc.
                     a_tag['href'] = f"{base_url}{href}"
                elif href.startswith('#'): # Page-internal fragment link
                    a_tag.unwrap() # De-link it, keeping the text
                else: # External link, mailto, javascript, etc.
                    a_tag.unwrap() # De-link it, keeping the text
            
            # Remove empty p tags that might result from unwrapping or decomposition
            for p_tag in parser_output_div.find_all('p'):
                if not p_tag.get_text(strip=True) and not p_tag.find_all(True, recursive=False): # No text and no child elements
                    p_tag.decompose()

            return str(parser_output_div)

    except httpx.HTTPStatusError as e:
        return f"<p>Error fetching page '{page_title}': HTTP {e.response.status_code} - {e.response.reason_phrase}</p>"
    except httpx.RequestError as e:
        return f"<p>Error fetching page '{page_title}': {str(e)}</p>"
    except Exception as e:
        # For unexpected errors, it's good to log them server-side as well
        # import logging
        # logging.exception(f"Unexpected error processing {page_title}")
        return f"<p>An unexpected error occurred while processing page '{page_title}'.</p>"


@mcp.tool()
async def extract_all_wikipedia_links(page_title: str, titles_only: bool = True) -> List[str]:
    """
    Fetches a Wikipedia page and extracts all unique links to other Wikipedia articles.

    Args:
        page_title: The title of the Wikipedia page (e.g., "Python (programming language)").
        titles_only: If True (default), returns only the page titles (e.g., "Python (programming language)").
                     If False, returns full URLs (e.g., "https://en.wikipedia.org/wiki/Python_(programming_language)").

    Returns:
        A list of unique Wikipedia page titles or full URLs, or a list with an error message if fetching/parsing fails.
    """
    formatted_title = page_title.replace(" ", "_")
    base_url = "https://en.wikipedia.org"
    url = f"{base_url}/wiki/{formatted_title}"
    
    links = [] # preserve order (and duplicates) in the essence of the wikipedia race game

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                if href.startswith('/wiki/'):
                    # Extract the part after /wiki/ and before any # or ?
                    path_segment = href.split('/wiki/', 1)[1]
                    main_path_part = path_segment.split('#')[0].split('?')[0]

                    # Filter out special pages (those with a colon in the main path part) and Main_Page
                    if ':' not in main_path_part and main_path_part != "Main_Page":
                        # Decode URL-encoded characters and replace underscores with spaces for the title
                        link_title = urllib.parse.unquote(main_path_part).replace('_', ' ')
                        
                        if titles_only:
                            links.append(link_title)
                        else:
                            links.append(f"{base_url}/wiki/{main_path_part}")
            
            if not links and page_title: # If no links found but page was presumably valid
                # This could happen on very sparse pages or if filtering is too aggressive
                # For this minimal tool, we return an empty list in such valid cases.
                pass # Intentional: return empty list if no valid links found on a fetched page

            return links

    except httpx.HTTPStatusError as e:
        return [f"Error fetching page '{page_title}': HTTP {e.response.status_code} - {e.response.reason_phrase}"]
    except httpx.RequestError as e:
        return [f"Error fetching page '{page_title}': {str(e)}"]
    except Exception as e:
        return [f"An unexpected error occurred while processing page '{page_title}': {str(e)}"]


if __name__ == "__main__":
    # This allows running the server directly using "python server.py"
    # For development, "mcp dev server.py" is usually preferred.
    mcp.run() 