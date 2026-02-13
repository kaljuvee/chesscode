"""Web search tools for chess content.

Stubs for future implementation - Lichess API, web search, etc.
"""
from typing import List, Dict


async def search_lichess(query: str, limit: int = 5) -> List[Dict]:
    """Search Lichess open database for games/positions.

    TODO: Implement with httpx + Lichess API.
    """
    return []


async def search_web(query: str) -> str:
    """General web search for chess articles and resources.

    TODO: Implement with web search API.
    """
    return "Web search not yet configured."
