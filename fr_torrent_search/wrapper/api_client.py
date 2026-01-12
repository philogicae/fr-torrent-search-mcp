import concurrent.futures
import importlib
import inspect
import logging
import pkgutil
from pathlib import Path
from sys import argv
from typing import Any

from .api.base import BaseTorrentApi
from .models import Torrent

logger = logging.getLogger(__name__)


class FrTorrentApi(BaseTorrentApi):
    """
    An aggregator client that automatically discovers and uses all available torrent APIs.
    """

    def __init__(self) -> None:
        # Initialize with a dummy URL as it's an aggregator
        super().__init__("http://aggregator")
        self.apis: list[BaseTorrentApi] = []
        self.api_names: list[str] = []
        self._initialized = False

    def _ensure_initialized(self) -> None:
        """Ensure that APIs are discovered and initialized."""
        if not self._initialized:
            self._discover_apis()
            self._initialized = True

    def _discover_apis(self) -> None:
        """Dynamically discover and instantiate all BaseTorrentApi subclasses in the api/ directory."""
        api_pkg_path = Path(__file__).parent / "api"
        for _, name, is_pkg in pkgutil.iter_modules([str(api_pkg_path)]):
            if is_pkg or name == "base":
                continue

            try:
                module_name = f"fr_torrent_search.wrapper.api.{name}"
                module = importlib.import_module(module_name)
                for _, obj in inspect.getmembers(module):
                    if (
                        inspect.isclass(obj)
                        and issubclass(obj, BaseTorrentApi)
                        and obj is not BaseTorrentApi
                    ):
                        try:
                            api_instance = obj()
                            if not api_instance.enabled:
                                continue
                            self.apis.append(api_instance)
                            self.api_names.append(api_instance.name)
                            logger.info(
                                f"Discovered and initialized API: {api_instance.name}"
                            )
                        except Exception as e:
                            logger.warning(
                                f"Failed to initialize API class {obj.__name__} from {name}: {e}"
                            )
            except Exception as e:
                logger.error(f"Failed to load module {name}: {e}")

    def _format_torrent(self, torrent: dict[str, Any]) -> Torrent:
        # This is not used by the aggregator directly as it delegates to sub-apis
        raise NotImplementedError("Aggregator does not format torrents directly")

    def search_torrents(self, query: str, max_items: int = 10) -> list[Torrent]:
        """
        Search for torrents across all discovered APIs in parallel.
        """
        self._ensure_initialized()
        all_results: list[Torrent] = []
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=len(self.apis)
        ) as executor:
            future_to_api = {
                executor.submit(api.search_torrents, query, max_items): api
                for api in self.apis
            }
            for future in concurrent.futures.as_completed(future_to_api):
                api = future_to_api[future]
                try:
                    results = future.result()
                    if results:
                        all_results.extend(results)
                except Exception as e:
                    logger.error(f"API {api.__class__.__name__} search failed: {e}")

        # Sort combined results by seeders (descending)
        all_results.sort(key=lambda x: x.seeders, reverse=True)
        return all_results[:max_items]

    def _get_api_for_id(self, torrent_id: str) -> BaseTorrentApi | None:
        """Find the API that matches the torrent ID prefix."""
        for api in self.apis:
            if api.id_prefix and torrent_id.startswith(api.id_prefix):
                return api
        return None

    def download_torrent_file_bytes(self, torrent_id: str) -> bytes | None:
        self._ensure_initialized()
        api = self._get_api_for_id(torrent_id)
        if api:
            return api.download_torrent_file_bytes(torrent_id)
        return None

    def download_torrent_file(
        self, torrent_id: str, output_dir: str | Path | None = None
    ) -> str | None:
        self._ensure_initialized()
        api = self._get_api_for_id(torrent_id)
        if api:
            return api.download_torrent_file(torrent_id, output_dir)
        return None

    def get_magnet_link(self, torrent_id: str) -> str | None:
        self._ensure_initialized()
        api = self._get_api_for_id(torrent_id)
        if api:
            return api.get_magnet_link(torrent_id)
        return None

    def get_torrent(self, torrent_id: str, **kwargs) -> str | bytes | None:
        """
        Get a specific torrent by delegating to the appropriate API.
        """
        self._ensure_initialized()
        api = self._get_api_for_id(torrent_id)
        if api:
            return api.get_torrent(torrent_id, **kwargs)
        return None

    def status(self) -> dict[str, Any] | None:
        """Check status of all APIs."""
        self._ensure_initialized()
        statuses = {}
        for api in self.apis:
            try:
                statuses[api.__class__.__name__] = api.status() or "Unavailable"
            except Exception as e:
                statuses[api.__class__.__name__] = f"Error: {e}"
        return statuses


if __name__ == "__main__":
    # Configure logging for direct execution
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
    QUERY = argv[1] if len(argv) > 1 else 0
    if not QUERY:
        print("Please provide a search query.")
        exit(1)
    client = FrTorrentApi()
    print(f"Status: {client.status()}")
    found_torrents: list[Torrent] = client.search_torrents(str(QUERY), 3)
    if found_torrents:
        print(f"Found {len(found_torrents)} torrents:")
        for t in found_torrents:
            print(f"- {t.filename} ({t.id})")

        first_id = found_torrents[0].id
        print(f"\nFetching first torrent: {first_id}")
        result = client.get_torrent(first_id)
        print(f"Result: {result}")
    else:
        print("No torrents found")
