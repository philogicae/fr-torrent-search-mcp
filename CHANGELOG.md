## [1.0.5] - 2026-01-13

### 💼 Changes

- Init
- Change default max_items from 20 to 10 in search endpoint
- Replace hardcoded test IDs with 'fake_id' and add lazy API initialization
- Remove deploy replicas configuration from compose.yaml
- Add Docker Hub publishing workflow and bump version to 1.0.2
- Update Docker image name to fr-torrent-search-mcp and bump version to 1.0.3
- Update CHANGELOG version from 1.0.0 to 1.0.3
- Add configurable torrent download folder and fix API endpoint paths

- Add FOLDER_TORRENT_FILES environment variable to configure torrent file download location (default: ./torrents)
- Change API endpoints from plural /torrents/* to singular /torrent/* for consistency
- Make output_dir parameter optional in download_torrent_file methods, defaulting to configured folder
- Add torrents folder to .gitignore
- Fix test fixture scope and add monkeypatch_session parameter
- Implement lazy initialization
- Add persistent volume for torrent files and fix eager initialization

- Add torrents volume to compose.yaml with mount to configured FOLDER_TORRENT_FILES path
- Remove eager initialization from FrTorrentApi constructor
- Add explicit _ensure_initialized() calls in FastAPI and MCP server entry points
- Rename _ensure_initialized to ensure_initialized and improve MCP tool return types

- Make ensure_initialized() public by removing underscore prefix
- Update all calls to use new public method name
- Change MCP tool return types from str | None to str for better type safety
- Add fallback error message in download_torrent_file MCP tool
- Move monkeypatch_session fixture definition before its usage in conftest.py
- Remove unused monkeypatch_session parameter from mock_torrent_apis fixture
- Update CHANGELOG version from 1.0.3 to 1.0.4
- Add documentation for FOLDER_TORRENT_FILES and update FastAPI endpoints

- Add FOLDER_TORRENT_FILES environment variable documentation in README
- Update FastAPI endpoints documentation with detailed descriptions
- Fix command example from fr-torrent-search-mcp to fr_torrent_search
- Add max_items parameter to search_torrents example
- Change FastAPI port mapping from 8787:8000 to 8000:8000 in compose.yaml
- Rename environment variables and refactor API configuration

- Fix sub APIs
- Rename YGG_BASE_URL to YGG_LOCAL_API for clarity
- Remove unused LA_CALE_TRACKER environment variable
- Add YGG_LOCAL_API to compose.yaml environment for service communication
- Consolidate torrent file download logic in BaseTorrentApi base class
- Add cli() method to BaseTorrentApi for command line testing
- Improve mock torrent data generation using bencodepy in tests
- Update test IDs from y_/c_ prefixes to yt_/lc_ for consistency
