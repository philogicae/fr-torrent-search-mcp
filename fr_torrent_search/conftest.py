from os import getcwd
from unittest.mock import patch

import pytest
import requests
from _pytest.monkeypatch import MonkeyPatch
from bencodepy import encode


@pytest.fixture(scope="session")
def monkeypatch_session():
    """Session-scoped monkeypatch."""
    m = MonkeyPatch()
    yield m
    m.undo()


@pytest.fixture(autouse=True, scope="session")
def mock_env(monkeypatch_session):
    """Set up environment variables for testing."""
    monkeypatch_session.setenv("FOLDER_TORRENT_FILES", getcwd())
    monkeypatch_session.setenv("LA_CALE_API_KEY", "mock_passkey")


@pytest.fixture(autouse=True, scope="session")
def mock_torrent_apis():
    """Mock La Cale API responses for local testing."""
    with patch("requests.Session.request") as mock_request:

        def side_effect(method, url, *args, **kwargs):
            mock_response = requests.Response()
            mock_response.status_code = 200
            mock_response.headers = {"Content-Type": "application/json"}
            mock_torrent_bytes = encode(
                {
                    "announce": "http://fake.tracker.com:80/announce",
                    "info": {
                        "name": "Berserk_Complete",
                        "piece length": 262144,
                        "pieces": b"0" * 20,
                        "files": [
                            {"length": 85048576, "path": ["Berserk.mkv"]},
                        ],
                    },
                }
            )

            # La Cale API (la-cale.space)
            if "la-cale.space" in url:
                if "/api/external" in url:
                    mock_response._content = b'[{"infoHash": "fake_id", "title": "Berserk La Cale Mock", "category": "Animation", "size": 629145600, "seeders": 150, "leechers": 20, "pubDate": "2023-11-15T12:00:00Z", "downloadLink": ".../api/download/fake_id?token=fake_token"}]'
                elif "/api/download/" in url:
                    mock_response.headers = {"Content-Type": "application/x-bittorrent"}
                    mock_response._content = mock_torrent_bytes
                else:
                    mock_response.status_code = 404
                return mock_response

            # Fallback for other requests
            mock_response.status_code = 404
            return mock_response

        mock_request.side_effect = side_effect
        yield mock_request
