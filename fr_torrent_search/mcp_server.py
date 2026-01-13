import logging
from typing import Any

from fastmcp import FastMCP

from .wrapper import FrTorrentApi

logger = logging.getLogger(__name__)
mcp: FastMCP[Any] = FastMCP("Fr Torrent Search")


client = FrTorrentApi()
client.ensure_initialized()


@mcp.tool()
def search_torrents(
    user_intent: str,
    query: str,
    max_items: int = 10,
) -> str:
    """Perfom an advanced torrent search across multiple providers.

    # Arguments:
    - `user_intent`: Must reflect user's overall intention (e.g., "last episode of Breaking Bad", "season 5 of Breaking Bad", "complete Breaking Bad series").
    - `query`: Optimized keywords for search. MUST be lowercase and space-separated.

    # Query Construction Rules:
    - **NO** generic terms: remove "movie", "series", "torrent", "download".
    - **NO** filler words: remove "the", "a", "an", "and", "of", "with".
    - **NO** technical tags: do NOT add "1080p", "x264", "bluray", or episode titles.
    - **TV Shows**:
        - Specific episode: `[show name] sXXeYY` (e.g., "shogun s01e05")
        - Full season: `[show name] sXX` (e.g., "shogun s01")
        - Full series: `[show name]` (e.g., "shogun")
    - **Language**: Add `multi` ONLY if the user specifically requests a non-French or multi-language version.

    # Result Analysis & Ranking:
    1. **Quality**: Prefer 1080p over 720p or 4k (unless requested).
    2. **Efficiency**: Prefer x265/HEVC for better quality/size ratio.
    3. **Health**: Maximize seeders + leechers.
    4. **Size**: Prefer smaller files within the same quality bracket.

    # Response Requirements:
    - Recommend the **top 3** results maximum.
    - For each recommendation, include: Filename, Size, Seeds/Leechs, Date, Source, and a 1-sentence "Why this?" reason.
    - If results are poor or irrelevant, suggest specific keywords to improve the search.
    """
    _ = user_intent
    logger.info(
        f"Searching for torrents: {query} (intent: {user_intent}), max_items: {max_items}"
    )
    torrents = client.search_torrents(query, max_items)
    return "\n".join([str(torrent) for torrent in torrents])


@mcp.tool()
def get_torrent(torrent_id: str) -> str:
    """Get a specific torrent (either magnet link or torrent file path) by id."""
    logger.info(f"Getting torrent for: {torrent_id}")
    result = client.get_torrent(torrent_id)
    if isinstance(result, bytes):
        return "Received raw bytes, not supported via this tool."
    return result or "Torrent not found"


@mcp.tool()
def get_magnet_link(torrent_id: str) -> str:
    """Get the magnet link for a specific torrent by id."""
    logger.info(f"Getting magnet link for torrent: {torrent_id}")
    magnet_link = client.get_magnet_link(torrent_id)
    return magnet_link or "Magnet link not found"


@mcp.tool()
def download_torrent_file(torrent_id: str, output_dir: str | None = None) -> str:
    """Download the torrent file for a specific torrent by id."""
    logger.info(f"Downloading torrent file for torrent: {torrent_id}")
    result = client.download_torrent_file(torrent_id, output_dir)
    return result or "Failed to download torrent file"
