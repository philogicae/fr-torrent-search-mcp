import logging
from pathlib import Path
from typing import Any

from ..models import Torrent
from ..utils import (
    ensure_folder,
    format_date,
    format_size,
    get_env,
    get_folder_torrent_files,
)
from .base import BaseTorrentApi

logger = logging.getLogger(__name__)


class LaCaleApi(BaseTorrentApi):
    """A client for interacting with the LaCale API."""

    name: str = "LaCale"
    id_prefix: str = "lc_"

    def __init__(self, base_url: str | None = None) -> None:
        """Initializes the API client."""
        super().__init__(
            base_url or str(get_env("LA_CALE_DOMAIN", "https://la-cale.space"))
        )
        self.apikey = get_env("LA_CALE_API_KEY")
        self.enabled = bool(self.apikey)
        if not self.apikey:
            logger.warning(
                "LA_CALE_API_KEY not found in .env file. La Cale will be disabled."
            )

    def _format_torrent(self, torrent: dict[str, Any]) -> Torrent:
        """Converts a torrent data dictionary from the API into a Torrent model instance."""
        return Torrent(
            id=(
                "N/A"
                if "downloadLink" not in torrent
                else f"{self.id_prefix}{torrent.get('downloadLink', '').split('/api/download/', 1)[-1]}"
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
            params={"q": query, "apikey": self.apikey},
        )
        if torrents:
            all_results = [self._format_torrent(torrent) for torrent in torrents]
            all_results.sort(key=lambda x: x.seeders, reverse=True)
            return all_results[:max_items]
        return []

    def download_torrent_file_bytes(self, torrent_id: str) -> bytes | None:
        """
        Download the .torrent file.
        Corresponds to GET /api/download/<<infoHash>?token=<token>>

        Args:
            torrent_id: The ID of the torrent.

        Returns:
            The .torrent file content as bytes or None.
        """
        info_hash, token = torrent_id[len(self.id_prefix) :].split("?token=", 1)
        torrent_bytes = self._request(
            "GET",
            f"/api/download/{info_hash}",
            params={
                "apikey": self.apikey,
                "token": token,
            },
        )
        if torrent_bytes:
            return torrent_bytes
        return None

    def download_torrent_file(
        self, torrent_id: str, output_dir: str | Path | None = None
    ) -> str | None:
        """
        Download the .torrent file.

        Args:
            torrent_id: The ID of the torrent.
            output_dir: The directory to save the .torrent file.

        Returns:
            The filename of the downloaded .torrent file or None.
        """
        try:
            filename = torrent_id.split("?token=", 1)[0] + ".torrent"
            torrent_bytes = self.download_torrent_file_bytes(torrent_id)
            if torrent_bytes and isinstance(torrent_bytes, bytes):
                with open(
                    str(
                        Path(ensure_folder(output_dir) or get_folder_torrent_files())
                        / filename
                    ),
                    "wb",
                ) as f:
                    f.write(torrent_bytes)
                return filename
        except NotImplementedError:
            logger.error(f"Not implemented for {self.name}")
        except Exception as e:
            logger.error(f"Error downloading torrent file for {torrent_id}: {e}")
        return None


if __name__ == "__main__":
    LaCaleApi().cli()
