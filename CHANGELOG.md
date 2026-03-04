## [1.2.0] - 2026-03-04

### 🚀 Features

- Feat: Deprecate YggTorrent support and migrate to La Cale API with token-based authentication

### 🐛 Bug Fixes

- Fix: Remove explicit fr_torrent_search path from CI workflow commands
- Fix: Remove pylint disable comments and refactor client initialization to lazy loading pattern

### 💼 Changes

- Update CHANGELOG version from 1.0.7 to 1.1.0
## [1.1.0] - 2026-02-05

### 🐛 Bug Fixes

- Fix: Deprecate La Cale support and update GitHub Actions workflow dependencies

### 💼 Changes

- Update CHANGELOG version from 1.0.6 to 1.0.7 and fix markdown formatting

- Add version 1.0.7 entry with consolidated changes from recent commits
- Fix escaped underscores in method names (_ensure_auth, _ensure_initialized)
- Fix asterisk escaping in API endpoint paths (/torrents/* to /torrent/*)
- Fix test ID prefix formatting (y_/c_ to yt_/lc_)
- Remove extra blank line between version 1.0.6 entries

### ⚙️ Miscellaneous Tasks

- Chore: Update version from 1.0.7 to 1.1.0
## [1.0.7] - 2026-01-18

### 💼 Changes

- Update CHANGELOG version from 1.0.5 to 1.0.6
- Fix typo in search_torrents docstring and improve query handling

- Fix typo "Perfom" to "Perform" in search_torrents MCP tool docstring
- Update query construction rules to allow technical tags when explicitly requested
- Simplify user_intent example and improve quality preference guidelines
- Change quality preference from "x265" to "h265" for consistency
- Remove preference against 4k quality in favor of 1080p or 4k over 720p
- Ensure query is lowercased in FrTorrentApi.search_torrents()
## [1.0.6] - 2026-01-15

### 💼 Changes

- Update CHANGELOG version from 1.0.4 to 1.0.5 and refactor git-cliff configuration

- Update CHANGELOG to version 1.0.5 with consolidated changes from previous releases
- Remove header and footer templates from cliff.toml
- Disable conventional commits parsing and filtering
- Change "Other" commit group to "Changes" for better clarity
- Remove trailing whitespace from changelog body template
- Add fail_on_unmatched_commit configuration option
- Fix topo_order_commits comment from "releases" to "commits"
- Add authentication checks and improve error handling across API implementations

- Add _ensure_auth() method to YggTorrentApi to verify authentication before requests
- Add get_user() endpoint to YggTorrentApi for authentication verification
- Add authentication checks to search_torrents() and download_torrent_file_bytes() in YggTorrentApi
- Improve status() methods to return consistent dict format with "OK"/"KO" status
- Move get_magnet_link() implementation from subclasses to BaseTorrentApi base
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
