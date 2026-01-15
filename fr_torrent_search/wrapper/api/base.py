import logging
from abc import ABC, abstractmethod
from pathlib import Path
from sys import argv
from typing import Any

from requests import Session, exceptions

from ..models import Mode, Torrent
from ..utils import ensure_folder, get_folder_torrent_files, torrent_bytes_to_magnet

logger = logging.getLogger(__name__)


class BaseTorrentApi(ABC):
    """An abstract base class for interacting with a torrent API."""

    name: str = ""
    id_prefix: str = ""
    enabled: bool = True
    order: list[Mode] = [Mode.FILE, Mode.MAGNET, Mode.BYTES]

    def __init__(self, base_url: str) -> None:
        """
        Initializes the API client.
        """
        self.base_url = base_url.lstrip("/")
        if not self.base_url.startswith("http"):
            self.base_url = f"https://{self.base_url}"
        self.session = Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
            }
        )

    def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        """
        Makes an HTTP request to the API.

        Args:
            method: HTTP method (GET, POST, etc.).
            endpoint: API endpoint path.
            params: URL query parameters.
            json_data: JSON body for POST/PUT requests.
            **kwargs: Additional arguments for request.

        Returns:
            The JSON response from the API or bytes for file downloads.

        Raises:
            exceptions.HTTPError: If the HTTP request returned an unsuccessful status code.
        """
        url = f"{self.base_url}/{endpoint.strip('/')}"
        try:
            response = self.session.request(
                method,
                url,
                params=params,
                json=json_data,
                allow_redirects=False,
                **kwargs,
            )

            # Handle redirects manually to catch magnet links
            if response.status_code in (301, 302, 303, 307, 308):
                location = response.headers.get("Location")
                if location and location.startswith("magnet:"):
                    return location
                # For normal HTTP redirects, follow them
                return self._request(
                    method, location, params=params, json=json_data, **kwargs
                )

            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "")
            if "application/json" in content_type:
                return response.json()
            elif response.content:
                return response.content
        except exceptions.RequestException as e:
            logger.error(f"Request to {url} failed: {e}")
        except Exception as e:
            logger.error(f"Exception on {url}: {e}")
        return None

    @abstractmethod
    def _format_torrent(self, torrent: dict[str, Any]) -> Torrent:
        """Converts a torrent data dictionary from the API into a Torrent model instance."""
        raise NotImplementedError()

    @abstractmethod
    def search_torrents(self, query: str, max_items: int = 10) -> list[Torrent]:
        """
        Get a list of torrents.

        Args:
            query: Search query.

        Returns:
            A list of torrent results.
        """
        raise NotImplementedError()

    @abstractmethod
    def download_torrent_file_bytes(self, torrent_id: str) -> bytes | None:
        """
        Download the .torrent file.

        Args:
            torrent_id: The ID of the torrent.

        Returns:
            The .torrent file content as bytes or None.
        """
        raise NotImplementedError()

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
            torrent_bytes = self.download_torrent_file_bytes(torrent_id)
            if torrent_bytes and isinstance(torrent_bytes, bytes):
                filename = f"{torrent_id}.torrent"
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

    def status(self) -> dict[str, Any]:
        """
        Get the status of the API.

        Returns:
            The status as a dictionary.
        """
        raise NotImplementedError()

    def get_torrent_as(
        self, torrent_id: str, mode: Mode | str, **kwargs
    ) -> str | bytes | None:
        """
        Get a specific torrent by mode.

        Args:
            torrent_id: The ID of the torrent.
            mode: The mode to use to get the torrent.

        Returns:
            The .torrent filename, magnet link, .torrent bytes or None.
        """
        _mode: Mode = Mode(mode) if isinstance(mode, str) else mode
        if mode not in self.order:
            logger.error(f"Invalid mode: {_mode.value}")
        else:
            try:
                if _mode == Mode.FILE:
                    return self.download_torrent_file(torrent_id, **kwargs)
                elif _mode == Mode.MAGNET:
                    return self.get_magnet_link(torrent_id)
                elif _mode == Mode.BYTES:
                    return self.download_torrent_file_bytes(torrent_id)
            except Exception as e:
                logger.error(
                    f"Failed to get torrent ({_mode.value}) for ID {torrent_id}: {e}"
                )
        return None

    def get_torrent(self, torrent_id: str, **kwargs) -> str | bytes | None:
        """
        Get a specific torrent.

        Args:
            torrent_id: The ID of the torrent.

        Returns:
            The .torrent filename, magnet link, .torrent bytes or None.
        """
        for mode in self.order:
            result = self.get_torrent_as(torrent_id, mode, **kwargs)
            if result:
                return result
        return None

    def cli(self):
        """
        Command line interface for the API.
        """
        query = argv[1] if len(argv) > 1 else None
        print(f"Status: {self.status()}")
        if query:
            found_torrents: list[Torrent] = self.search_torrents(query, max_items=100)
            if found_torrents:
                found_sources = set()
                for t in found_torrents:
                    found_sources.add(t.source)
                    print(
                        f"{t.id} ({t.seeders}|{t.leechers}|{t.downloads}) - {t.filename}"
                    )
                print(f"Fetching: {found_torrents[0].id}")
                print(
                    f"Result: {self.get_torrent_as(found_torrents[0].id, Mode.MAGNET)}"
                )
                print(
                    f"Found Sources: {found_sources} | Found Torrents: {len(found_torrents)}"
                )
            else:
                print("No torrents found")
        else:
            print("Please provide a search query.")
