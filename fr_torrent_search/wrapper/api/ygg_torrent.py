import logging
from typing import Any

from ..models import Torrent
from ..utils import (
    format_date,
    format_size,
    get_env,
    get_env_bool,
    torrent_bytes_to_magnet,
)
from .base import BaseTorrentApi

logger = logging.getLogger(__name__)


class YggTorrentApi(BaseTorrentApi):
    """A client for interacting with the YggTorrent API."""

    name: str = "YggTorrent"
    id_prefix: str = "yt_"

    def __init__(self, base_url: str | None = None) -> None:
        """
        Initializes the API client.
        """
        super().__init__(
            base_url or str(get_env("YGG_LOCAL_API", "http://localhost:8715"))
        )
        self.enabled = get_env_bool("YGG_ENABLE")
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
        """
        Download the .torrent file.
        Corresponds to GET /torrent/<id>

        Args:
            torrent_id: The ID of the torrent.

        Returns:
            The .torrent file content as bytes or None.
        """
        torrent_bytes = self._request(
            "GET", f"torrent/{torrent_id[len(self.id_prefix) :]}"
        )
        if torrent_bytes:
            return torrent_bytes
        return None

    def get_magnet_link(self, torrent_id: str) -> str | None:
        """
        Get the magnet link for a specific torrent.

        Args:
            torrent_id: The ID of the torrent.

        Returns:
            The magnet link as a string or None.
        """
        try:
            torrent_bytes = self.download_torrent_file_bytes(torrent_id)
            if torrent_bytes and isinstance(torrent_bytes, bytes):
                return torrent_bytes_to_magnet(torrent_bytes)
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
    YggTorrentApi().cli()
