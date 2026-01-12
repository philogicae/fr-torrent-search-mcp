import logging
from os import getenv
from pathlib import Path
from sys import argv
from typing import Any

from dotenv import load_dotenv

from ..models import Torrent
from ..utils import format_date, format_size, torrent_bytes_to_magnet
from .base import BaseTorrentApi

load_dotenv()

logger = logging.getLogger(__name__)

LA_CALE_DOMAIN = getenv("LA_CALE_DOMAIN") or "https://la-cale.space"
LA_CALE_TRACKER = getenv("LA_CALE_TRACKER") or "https://tracker.la-cale.space/announce"
LA_CALE_ENABLE = getenv("LA_CALE_ENABLE", "1") not in ("0", "false", "False")


class LaCaleApi(BaseTorrentApi):
    """A client for interacting with the LaCale API."""

    name: str = "LaCale"
    id_prefix: str = "c_"

    def __init__(self, base_url: str = LA_CALE_DOMAIN) -> None:
        """
        Initializes the API client.
        """
        super().__init__(base_url)
        self.enabled = LA_CALE_ENABLE
        self.passkey = getenv("LA_CALE_PASSKEY")
        if not self.passkey:
            raise ValueError("LA_CALE_PASSKEY not found in .env file.")
        self.tracker = f"{LA_CALE_TRACKER}?passkey={self.passkey}"

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
            The .torrent file content as bytes or an error dictionary.
        """
        torrent_bytes = self._request(
            "GET",
            f"/api/torrents/download/{torrent_id[len(self.id_prefix) :]}",
            params={"passkey": self.passkey},
        )
        if torrent_bytes:
            return torrent_bytes
        return None

    def download_torrent_file(
        self, torrent_id: str, output_dir: str | Path = "."
    ) -> str | None:
        """
        Download the .torrent file.

        Args:
            torrent_id: The ID of the torrent.

        Returns:
            The filename of the downloaded .torrent file or None.
        """
        try:
            torrent_bytes = self.download_torrent_file_bytes(torrent_id)
            if torrent_bytes and isinstance(torrent_bytes, bytes):
                filename = f"{torrent_id}.torrent"
                with open(Path(output_dir) / filename, "wb") as f:
                    f.write(torrent_bytes)
                return filename
        except Exception as e:
            logger.error(f"Error downloading torrent file for {torrent_id}: {e}")
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
                return torrent_bytes_to_magnet(torrent_bytes, self.tracker)
        except Exception as e:
            logger.error(f"Failed to get magnet link for {torrent_id}: {e}")
        return None

    def status(self) -> dict[str, Any] | None:
        """
        Get the status of the API.
        Corresponds to a dummy GET /api/external

        Returns:
            The status as a dictionary or None.
        """
        torrents = self._request(
            "GET",
            "api/external",
            params={"passkey": self.passkey},
        )
        if torrents:
            return {"status": "ok"}
        return None


if __name__ == "__main__":
    QUERY = argv[1] if len(argv) > 1 else 0
    if not QUERY:
        print("Please provide a search query.")
        exit(1)
    client = LaCaleApi()
    found_torrents: list[Torrent] = client.search_torrents(str(QUERY), 3)
    if found_torrents:
        print(found_torrents)
        print(client.get_torrent(found_torrents[0].id))
    else:
        print("No torrents found")
