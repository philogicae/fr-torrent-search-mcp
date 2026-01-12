import logging
from os import getenv
from pathlib import Path
from sys import argv
from typing import Any

from dotenv import load_dotenv

from ..models import Mode, Torrent
from ..utils import format_date, format_size
from .base import BaseTorrentApi

load_dotenv()

logger = logging.getLogger(__name__)

YGG_BASE_URL = getenv("YGG_BASE_URL") or "http://localhost:8715"
YGG_ENABLE = getenv("YGG_ENABLE", "1") not in ("0", "false", "False")


class YggTorrentApi(BaseTorrentApi):
    """A client for interacting with the YggTorrent API."""

    name: str = "YggTorrent"
    order: list[Mode] = [Mode.MAGNET]
    id_prefix: str = "y_"

    def __init__(self, base_url: str = YGG_BASE_URL) -> None:
        """
        Initializes the API client.
        """
        super().__init__(base_url)
        self.enabled = YGG_ENABLE
        self._categories = None

    @property
    def categories(self) -> dict[int, str]:
        if self._categories is None:
            if not self.enabled:
                self._categories = {}
            elif not self.status():
                # We don't raise here anymore to avoid breaking initialization
                logger.warning("YggTorrent API is not available during category fetch.")
                self._categories = {}
            else:
                self._categories = self._fetch_categories()
        return self._categories

    def _fetch_categories(self) -> dict[int, str]:
        """Get a list of categories."""
        raw_categories = self._request("GET", "categories")
        if not raw_categories:
            return {}

        formatted_categories = {}

        def process_categories(
            categories: list[dict[str, Any]], parent_name: str = ""
        ) -> None:
            for cat in categories:
                cat_id = cat.get("id")
                cat_name = cat.get("name", "")
                full_name = f"{parent_name}/{cat_name}" if parent_name else cat_name
                if cat_id is not None:
                    formatted_categories[cat_id] = full_name
                sub_cats = cat.get("sub_categories")
                if sub_cats:
                    process_categories(sub_cats, full_name)

        process_categories(raw_categories)
        return formatted_categories

    def _format_torrent(self, torrent: dict[str, Any]) -> Torrent:
        """Converts a torrent data dictionary from the API into a Torrent model instance."""
        return Torrent(
            id="N/A" if "id" not in torrent else f"{self.id_prefix}{torrent.get('id')}",
            filename=torrent.get("name") or "N/A",
            category=self.categories.get(torrent.get("category_id") or 0) or "N/A",
            size=format_size(torrent.get("size")),
            seeders=torrent.get("seed") or 0,
            leechers=torrent.get("leech") or 0,
            downloads=torrent.get("completed") or 0,
            date=format_date(torrent.get("age_stamp")),
            magnet_link=None,
            source=self.name,
        )

    def search_torrents(self, query: str, max_items: int = 10) -> list[Torrent]:
        """
        Get a list of torrents.
        Corresponds to GET /search

        Args:
            query: Search query.

        Returns:
            A list of torrent results.
        """
        if not self.enabled:
            return []

        torrents = self._request(
            "GET", "search", params={"q": query, "sort": "seed", "order": "descending"}
        )
        if torrents:
            return [self._format_torrent(torrent) for torrent in torrents][:max_items]
        return []

    def download_torrent_file_bytes(self, torrent_id: str) -> bytes | None:
        raise NotImplementedError()

    def download_torrent_file(
        self, torrent_id: str, output_dir: str | Path | None = None
    ) -> str | None:
        raise NotImplementedError()

    def get_magnet_link(self, torrent_id: str) -> str | None:
        """
        Get the magnet link for a specific torrent.

        Args:
            torrent_id: The ID of the torrent.

        Returns:
            The magnet link as a string or None.
        """
        try:
            magnet_link = self._request(
                "GET", f"torrent/{torrent_id[len(self.id_prefix) :]}"
            )
            if magnet_link:
                return magnet_link
        except Exception as e:
            logger.error(f"Failed to get magnet link for {torrent_id}: {e}")
        return None

    def status(self) -> dict[str, Any] | None:
        """
        Get the status of the API.
        Corresponds to GET /status

        Returns:
            The status as a dictionary or None.
        """
        try:
            status = self._request("GET", "status")
            if status:
                return status
        except Exception as e:
            logger.error(f"Failed to get status: {e}")
        return None


if __name__ == "__main__":
    QUERY = argv[1] if len(argv) > 1 else 0
    if not QUERY:
        print("Please provide a search query.")
        exit(1)
    client = YggTorrentApi()
    found_torrents: list[Torrent] = client.search_torrents(str(QUERY), 3)
    if found_torrents:
        print(found_torrents)
        print(client.get_torrent(found_torrents[0].id))
    else:
        print("No torrents found")
