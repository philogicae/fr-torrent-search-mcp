# FR Torrent MCP Server & Wrapper

[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://docs.astral.sh/uv/getting-started/installation/)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![PyPI](https://badge.fury.io/py/fr-torrent-search-mcp.svg?cache-control=no-cache)](https://badge.fury.io/py/fr-torrent-search-mcp)
[![Actions status](https://github.com/philogicae/fr-torrent-search-mcp/actions/workflows/python-package-ci.yml/badge.svg?cache-control=no-cache)](https://github.com/philogicae/fr-torrent-search-mcp/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/philogicae/fr-torrent-search-mcp)

This repository provides a Python wrapper for the FR Torrent websites and an MCP (Model Context Protocol) server to interact with them programmatically. This allows for easy integration of FR Torrent functionalities into other applications or services.

<a href="https://glama.ai/mcp/servers/@philogicae/fr-torrent-search-mcp">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/@philogicae/fr-torrent-search-mcp/badge?cache-control=no-cache" alt="FR Torrent Server MCP server" />
</a>

## Quickstart

> [How to use it with MCP Clients](#via-mcp-clients)

> [Run it with Docker to bypass common DNS issues](#for-docker)

## Table of Contents

- [Features](#features)
- [Setup](#setup)
- [Prerequisites](#prerequisites)
- [Configuration](#configuration)
- [Installation](#installation)
- [Install from PyPI (Recommended)](#install-from-pypi-recommended)
- [For Local Development](#for-local-development)
- [For Docker](#for-docker)
- [Usage](#usage)
- [As Python Wrapper](#as-python-wrapper)
- [As MCP Server](#as-mcp-server)
- [As FastAPI Server](#as-fastapi-server)
- [Via MCP Clients](#via-mcp-clients)
- [Example with Windsurf](#example-with-windsurf)
- [Contributing](#contributing)
- [Changelog](#changelog)
- [License](#license)

## Features

- API aggregator for multiple French torrent providers:
  - **YggTorrent**: Support via local bridge [UwUDev/ygege](https://github.com/UwUDev/ygege), check [compose.yaml](./compose.yaml).
  - **La Cale**: Native support.
- MCP server interface for standardized communication (stdio, sse, streamable-http)
- FastAPI server interface for alternative HTTP access (e.g., for direct API calls or testing)
- Tools:
  - Search for torrents across all providers
  - Get torrent
    - Get magnet link
    - Download torrent file

## Setup

### Prerequisites

- Active account (for YggTorrent).
- Passkey (for LaCale).
- Python 3.10+ (required for PyPI install).
- [`uv`](https://github.com/astral-sh/uv) (for local development)
- Docker and Docker Compose (for Docker setup)

### Configuration

The application requires configuration for the supported providers.

1.  **Set Environment Variables**: The application reads configuration from environment variables. The recommended way is by creating a `.env` file in your project's root directory.

```env
# YGGTorrent Configuration
#YGG_ENABLE=0
#YGG_DOMAIN=www.yggtorrent.org
#YGG_LOCAL_API=http://localhost:8715  # Local Ygg API
YGG_USERNAME=
YGG_PASSWORD=
#TURBO_ENABLED=true

# LaCale Configuration
#LA_CALE_ENABLE=0
#LA_CALE_DOMAIN=la-cale.space
# Find your passkey on https://la-cale.space/profile
LA_CALE_PASSKEY=

# Target folder for torrent files (Default: ./torrents).
#FOLDER_TORRENT_FILES=/path/to/target/folder
```

### Installation

Choose one of the following installation methods.

#### Install from PyPI (Recommended)

This method is best for using the package as a library or running the server without modifying the code.

1.  Install the package from PyPI:

```bash
pip install fr-torrent-search-mcp
```

2.  Create a `.env` file in the directory where you'll run the application and add your configuration:

```env
YGG_USERNAME=your_ygg_username
YGG_PASSWORD=your_ygg_password
#TURBO_ENABLED=true
LA_CALE_PASSKEY=your_la_cale_passkey
#FOLDER_TORRENT_FILES=/path/to/target/folder
```

3.  Run the MCP server (default: stdio):

```bash
python -m fr_torrent_search
```

#### For Local Development

This method is for contributors who want to modify the source code.
Using [`uv`](https://github.com/astral-sh/uv):

1.  Clone the repository:

```bash
git clone https://github.com/philogicae/fr-torrent-search-mcp.git
cd fr-torrent-search-mcp
```

2.  Install dependencies using `uv`:

```bash
uv sync --locked
```

3.  Create your configuration file by copying the example and add your passkey:

```bash
cp .env.example .env
```

4.  Run the MCP server (default: stdio):

```bash
uv run -m fr_torrent_search
```

#### For Docker

This method uses Docker to run the server in a container.

[compose.yaml](./compose.yaml) is configured to bypass DNS issues (using [quad9](https://quad9.net/) DNS) and run a local Ygg API (Required for YggTorrent support).

1.  Clone the repository (if you haven't already):

```bash
git clone https://github.com/philogicae/fr-torrent-search-mcp.git
cd fr-torrent-search-mcp
```

2.  Create your configuration file by copying the example and add your passkey:

```bash
cp .env.example .env
```

3.  Build and run the container using Docker Compose (default port: 8000):

```bash
docker compose up --build -d
```

4.  Access container logs:

```bash
docker logs fr-torrent-search-mcp -f
```

## Usage

### As Python Wrapper

```python
from fr_torrent_search import fr_torrent_api

results = fr_torrent_api.search_torrents('...', max_items=10)
for torrent in results:
    print(f"{torrent.filename} | {torrent.size} | {torrent.seeders} SE | {torrent.leechers} LE | {torrent.downloads} DL | {torrent.date}")
```

### As MCP Server

```python
from fr_torrent_search import fr_torrent_mcp

fr_torrent_mcp.run(transport="sse")
```

### As FastAPI Server

This project also includes a FastAPI server as an alternative way to interact with the FR Torrent functionalities via a standard HTTP API. This can be useful for direct API calls, integration with other web services, or for testing purposes.

**Running the FastAPI Server:**

```bash
# With Python
python -m fr_torrent_search --mode fastapi
# With uv
uv run -m fr_torrent_search --mode fastapi
```

- `--host <host>`: Default: `0.0.0.0`.
- `--port <port>`: Default: `8000`.
- `--reload`: Enables auto-reloading when code changes (useful for development).
- `--workers <workers>`: Default: `1`.

The FastAPI server will then be accessible at `http://<host>:<port>`

**Available Endpoints:**
The FastAPI server exposes similar functionalities to the MCP server. Key endpoints include:

- `GET /`: Health check endpoint. Returns `{"status": "ok"}`.
- `POST /torrent/search`: Search for torrents (params: `query`, `max_items`).
- `GET /torrent/{torrent_id}`: Get torrent (returns magnet link or .torrent file).
- `GET /torrent/{torrent_id}/magnet`: Get magnet link for a torrent.
- `GET /torrent/{torrent_id}/file`: Download .torrent file.
- `GET /docs`: Interactive API documentation (Swagger UI).
- `GET /redoc`: Alternative API documentation (ReDoc).

Environment variables are configured the same way as for the MCP server.

### Via MCP Clients

Usable with any MCP-compatible client. Available tools:

- `search_torrents`: Search for torrents.
- `get_torrent`: Get torrent data (magnet or file).
- `get_magnet_link`: Get the magnet link for a torrent.
- `download_torrent_file`: Download the .torrent file for a torrent.

#### Example with Windsurf

Configuration:

```json
{
  "mcpServers": {
    ...
    # with sse transport (requires installation)
    "fr-torrent-search-mcp": {
      "serverUrl": "http://127.0.0.1:8000/sse"
    }
    # with streamable-http transport (requires installation)
    "fr-torrent-search-mcp": {
      "serverUrl": "http://127.0.0.1:8000/mcp" # not yet supported by every client
    }
    ...
  }
}
```

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a history of changes to this project.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
