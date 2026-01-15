import logging
from typing import Any

from ..models import Torrent
from ..utils import format_date, format_size, get_env, get_env_bool
from .base import BaseTorrentApi

logger = logging.getLogger(__name__)


class LaCaleApi(BaseTorrentApi):
    """A client for interacting with the LaCale API."""

    name: str = "LaCale"
    id_prefix: str = "lc_"

    def __init__(self, base_url: str | None = None) -> None:
        """
        Initializes the API client.
        """
        super().__init__(
            base_url or str(get_env("LA_CALE_DOMAIN", "https://la-cale.space"))
        )
        self.passkey = get_env("LA_CALE_PASSKEY")
        self.enabled = bool(self.passkey) and get_env_bool("LA_CALE_ENABLE")
        if not self.passkey:
            raise ValueError("LA_CALE_PASSKEY not found in .env file.")

    def _format_torrent(self, torrent: dict[str, Any]) -> Torrent:
        """Converts a torrent data dictionary from the API into a Torrent model instance."""
        return Torrent(
            id=(
                "N/A"
                if "infoHash" not in torrent
                else f"{self.id_prefix}{torrent.get('infoHash')}"
            ),
            filename=torrent.get("title") or "N/A",
            category=torrent.get("category") or "N/A",
            size=format_size(torrent.get("size")),
            seeders=torrent.get("seeders") or 0,
            leechers=torrent.get("leechers") or 0,
            downloads="N/A",
            date=format_date(torrent.get("pubDate")),
            magnet_link=None,
            source=self.name,
        )

    def search_torrents(self, query: str, max_items: int = 10) -> list[Torrent]:
        """
        Get a list of torrents.
        Corresponds to GET /api/external

        Args:
            query: Search query.

        Returns:
            A list of torrent results.
        """
        if not self.enabled:
            return []

        torrents = self._request(
            "GET",
            "api/external",
            params={"q": query, "passkey": self.passkey},
        )
        if torrents:
            all_results = [self._format_torrent(torrent) for torrent in torrents]
            all_results.sort(key=lambda x: x.seeders, reverse=True)
            return all_results[:max_items]
        return []

    def download_torrent_file_bytes(self, torrent_id: str) -> bytes | None:
        """
        Download the .torrent file.
        Corresponds to GET /api/torrents/download/<infoHash>

        Args:
            torrent_id: The ID of the torrent.

        Returns:
            The .torrent file content as bytes or None.
        """
        torrent_bytes = self._request(
            "GET",
            f"/api/torrents/download/{torrent_id[len(self.id_prefix) :]}",
            params={"passkey": self.passkey},
        )
        if torrent_bytes:
            return torrent_bytes
        return None

    def status(self) -> dict[str, Any]:
        """
        Get the status of the API.
        Corresponds to a dummy GET /api/external

        Returns:
            The status as a dictionary.
        """
        torrents = self._request(
            "GET",
            "api/external",
            params={"passkey": self.passkey},
        )
        if torrents:
            return {"status": "OK"}
        return {"status": "KO"}


if __name__ == "__main__":
    LaCaleApi().cli()
