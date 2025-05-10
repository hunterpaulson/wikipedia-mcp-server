# Wikipedia MCP Server

A Model Context Protocol (MCP) server that provides tools to fetch and format Wikipedia content for The Wiki Game where models can compete in time/clicks go from one wikipedia page to another.

## Overview

This server exposes several tools that can:
- Fetch the main text content and a list of internal links from a Wikipedia page.
- Provide a "game-friendly" HTML version of a Wikipedia page, where only internal article links are active, designed for experiences like the "Wikipedia race game."
- Extract all unique Wikipedia article links from a page, with options to return full URLs or just page titles to minimize token usage.

It uses `httpx` for asynchronous HTTP requests and `BeautifulSoup4` for HTML parsing.

## Features

- **Structured Content Extraction**: Get clean text and a list of internal links from any Wikipedia page.
- **Wikipedia Race Game Support**: Fetch a version of a Wikipedia page tailored for "click-based" navigation games, with external links and clutter removed.
- **Minimal Link Extraction**: Efficiently retrieve all Wikipedia article links from a page, returning either full URLs or just titles.
- **Asynchronous Operations**: Built with `async` and `httpx` for non-blocking network requests.

## Prerequisites

- Python 3.12+
- `mcp[cli]` library
- `httpx` library
- `beautifulsoup4` library

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/hunterpaulson/wikipedia-mcp-server.git
    cd wikipedia-mcp-server
    ```

2.  **Set up a Python virtual environment (recommended):**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows use `.\.venv\Scripts\activate`
    ```

3.  **Install the project and its dependencies:**
    The project uses `pyproject.toml` to define its dependencies.

    If you are using `uv`:
    ```bash
    uv pip install -e .
    ```
    This command installs the project in "editable" mode, which is convenient for development. It will automatically pick up dependencies listed in `pyproject.toml`.

    Alternatively, using `pip`:
    ```bash
    pip install -e .
    ```
    This also installs the project in editable mode.

## Running the Server

You can run the MCP server in a couple of ways:

1.  **Using the MCP development tool (recommended for development):**
    This provides an inspector UI to easily test your tools.
    ```bash
    mcp dev server.py
    ```

2.  **Directly executing the Python script:**
    ```bash
    python server.py
    ```

## Available MCP Tools

Once the server is running, the following tools will be available to compatible MCP clients (e.g., via the MCP Inspector started with `mcp dev`):

### 1. `fetch_wikipedia_page`

Fetches the main text content and internal links of a Wikipedia page.

-   **Arguments**:
    -   `page_title` (str): The title of the Wikipedia page (e.g., "Python (programming language)").
-   **Returns**: (Dict)
    A dictionary containing:
    -   `"main_text"`: The main article text.
    -   `"wikipedia_links"`: A list of full URLs to other Wikipedia articles found on the page.
    Or, in case of an error:
    -   `"error"`: A string describing the error.
    -   `"main_text"`: Empty string.
    -   `"wikipedia_links"`: Empty list.
-   **Example Call (in MCP Inspector)**:
    -   Tool: `fetch_wikipedia_page`
    -   `page_title`: `"Artificial intelligence"`

### 2. `fetch_next_wikipedia_page`

Fetches and processes a Wikipedia page for the "Wikipedia race game." Returns HTML content where only internal Wikipedia article links are active. References, external links, and non-essential elements (like navboxes, category links, edit links) are removed or de-linked. Infoboxes (sidebars with summary information) are preserved.

-   **Arguments**:
    -   `page_title` (str): The title of the Wikipedia page (e.g., "Philosophy").
-   **Returns**: (str)
    An HTML string of the processed page content, suitable for rendering in a simple web view for the game.
    In case of an error, returns an HTML string containing the error message (e.g., `<p>Error fetching page...</p>`).
-   **Example Call (in MCP Inspector)**:
    -   Tool: `fetch_next_wikipedia_page`
    -   `page_title`: `"Game theory"`

### 3. `extract_all_wikipedia_links`

Fetches a Wikipedia page and extracts all unique links to other Wikipedia articles found anywhere on the page.

-   **Arguments**:
    -   `page_title` (str): The title of the Wikipedia page (e.g., "World Wide Web").
    -   `titles_only` (bool, optional, default: `True`):
        -   If `True`, returns only the page titles (e.g., "Tim Berners-Lee").
        -   If `False`, returns full URLs (e.g., "https://en.wikipedia.org/wiki/Tim_Berners-Lee").
-   **Returns**: (List[str])
    A list of unique Wikipedia page titles or full URLs.
    If an error occurs, returns a list containing a single string with the error message.
-   **Example Call (in MCP Inspector)**:
    -   Tool: `extract_all_wikipedia_links`
    -   `page_title`: `"Hypertext Transfer Protocol"`
    -   `titles_only`: `True`  (or `False` to get full URLs)

## Development Notes

-   The server is configured using `FastMCP` from the `mcp` library.
-   HTML parsing relies on specific Wikipedia page structures (e.g., `div#mw-content-text`, `div.mw-parser-output`). Significant changes to Wikipedia's layout might require updates to the parsing logic.
-   Error handling is included for HTTP issues and unexpected exceptions during processing.

---
