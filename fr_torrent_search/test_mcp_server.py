from os import getcwd, path, remove
from typing import Any

import pytest
from fastmcp import Client

from .mcp_server import mcp


@pytest.fixture(scope="session")
def mcp_client() -> Client[Any]:
    """Create a FastMCP client for testing."""
    return Client(mcp)


@pytest.mark.asyncio
async def test_search_torrents(mcp_client: Client[Any]) -> None:
    """Test the 'search_torrents' tool."""
    async with mcp_client as client:
        result = await client.call_tool(
            "search_torrents",
            {"user_intent": "berserk series", "query": "berserk", "max_items": 3},
        )
        assert result is not None and len(result.content[0].text) > 32


@pytest.mark.asyncio
async def test_get_torrent(mcp_client: Client[Any]) -> None:
    """Test the 'get_torrent' tool."""
    async with mcp_client as client:
        result = await client.call_tool("get_torrent", {"torrent_id": "yt_fake_id"})
        assert result is not None and len(result.content[0].text) > 10
        file_path = path.join(getcwd(), result.content[0].text)
        if path.exists(file_path):
            remove(file_path)


@pytest.mark.asyncio
async def test_get_magnet_link(mcp_client: Client[Any]) -> None:
    """Test the 'get_magnet_link' tool."""
    async with mcp_client as client:
        result = await client.call_tool("get_magnet_link", {"torrent_id": "yt_fake_id"})
        assert result is not None and len(result.content[0].text) > 32


@pytest.mark.asyncio
async def test_download_torrent_file(mcp_client: Client[Any]) -> None:
    """Test the 'download_torrent_file' tool."""
    async with mcp_client as client:
        curr_dir = getcwd()
        result = await client.call_tool(
            "download_torrent_file",
            {
                "torrent_id": "lc_fake_id",
                "output_dir": curr_dir,
            },
        )
        assert result is not None and len(result.content[0].text) > 10
        file_path = path.join(curr_dir, result.content[0].text)
        if path.exists(file_path):
            remove(file_path)
