import logging
from typing import Any

from ..models import Torrent
from ..utils import format_date, format_size, get_env, get_env_bool
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
        if not self._ensure_auth():
            logger.warning("Failed to authenticate to YggTorrent API.")
            return {}
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

    def get_user(self) -> dict[str, Any]:
        """
        Get the user information.
        Corresponds to GET /user.

        Returns:
            The user as a dictionary.
        """
        user = self._request("GET", "user")
        if user:
            return user
        return {"status": "KO"}

    def _ensure_auth(self) -> bool:
        """
        Ensure authentication.
        Calls get_user() that re-authenticate automatically if needed.

        Returns:
            True if the user is authenticated, False otherwise.
        """
        return self.get_user().get("username") is not None

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
        if not self._ensure_auth():
            logger.warning("Failed to authenticate to YggTorrent API.")
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
        if not self._ensure_auth():
            logger.warning("Failed to authenticate to YggTorrent API.")
            return None
        torrent_bytes = self._request(
            "GET", f"torrent/{torrent_id[len(self.id_prefix) :]}"
        )
        if torrent_bytes:
            return torrent_bytes
        return None

    def status(self) -> dict[str, Any]:
        """
        Get the status of the API.
        Corresponds to GET /status

        Returns:
            The status as a dictionary.
        """
        if not self._ensure_auth():
            logger.warning("Failed to authenticate to YggTorrent API.")
        else:
            status = self._request("GET", "status")
            if status:
                return status
        return {"status": "KO"}


if __name__ == "__main__":
    YggTorrentApi().cli()
