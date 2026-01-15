import concurrent.futures
import importlib
import inspect
import logging
import pkgutil
from pathlib import Path
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

    def ensure_initialized(self) -> None:
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

    def search_torrents(
        self, query: str, max_items: int = 10, exclude: list[str] | None = None
    ) -> list[Torrent]:
        """
        Search for torrents across all discovered APIs in parallel.

        Args:
            query: Search query string
            max_items: Maximum number of results to return
            exclude: List of API names to exclude from search
        """
        self.ensure_initialized()
        all_results: list[Torrent] = []

        # Filter APIs based on exclude list
        apis_to_use = self.apis
        if exclude:
            apis_to_use = [api for api in self.apis if api.name not in exclude]

        # If no APIs available after filtering, return empty list
        if not apis_to_use:
            return []

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=len(apis_to_use)
        ) as executor:
            future_to_api = {
                executor.submit(api.search_torrents, query, max_items): api
                for api in apis_to_use
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
        self.ensure_initialized()
        api = self._get_api_for_id(torrent_id)
        if api:
            return api.download_torrent_file_bytes(torrent_id)
        return None

    def download_torrent_file(
        self, torrent_id: str, output_dir: str | Path | None = None
    ) -> str | None:
        self.ensure_initialized()
        api = self._get_api_for_id(torrent_id)
        if api:
            return api.download_torrent_file(torrent_id, output_dir)
        return None

    def get_magnet_link(self, torrent_id: str) -> str | None:
        self.ensure_initialized()
        api = self._get_api_for_id(torrent_id)
        if api:
            return api.get_magnet_link(torrent_id)
        return None

    def get_torrent(self, torrent_id: str, **kwargs) -> str | bytes | None:
        """
        Get a specific torrent by delegating to the appropriate API.
        """
        self.ensure_initialized()
        api = self._get_api_for_id(torrent_id)
        if api:
            return api.get_torrent(torrent_id, **kwargs)
        return None

    def status(self) -> dict[str, Any]:
        """Check status of all APIs."""
        self.ensure_initialized()
        statuses = {}
        for api in self.apis:
            try:
                statuses[api.__class__.__name__] = api.status() or {"status": "KO"}
            except Exception:
                statuses[api.__class__.__name__] = {"status": "KO"}
        return statuses


if __name__ == "__main__":
    FrTorrentApi().cli()
