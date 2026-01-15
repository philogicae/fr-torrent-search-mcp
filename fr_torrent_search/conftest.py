# pylint: disable=protected-access
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
def mock_env(monkeypatch_session):  # pylint: disable=redefined-outer-name
    """Set up environment variables for testing."""
    monkeypatch_session.setenv("FOLDER_TORRENT_FILES", getcwd())
    monkeypatch_session.setenv("YGG_LOCAL_API", "http://localhost:8715")
    monkeypatch_session.setenv("LA_CALE_PASSKEY", "mock_passkey")


@pytest.fixture(autouse=True, scope="session")
def mock_torrent_apis():
    """Mock YGG and La Cale API responses for local testing."""
    with patch("requests.Session.request") as mock_request:

        def side_effect(method, url, *args, **kwargs):  # pylint: disable=unused-argument
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

            # YGG API (localhost:8715 or specific IP)
            if ":8715" in url:
                if url.endswith("/status"):
                    mock_response._content = b'{"status": "ok"}'
                elif url.endswith("/user"):
                    mock_response._content = b'{"username": "test"}'
                elif url.endswith("/categories"):
                    mock_response._content = b'[{"id": 1, "name": "Film", "sub_categories": [{"id": 2, "name": "Animation"}]}, {"id": 3, "name": "S\xc3\xa9rie"}]'
                elif "/search" in url:
                    mock_response._content = b'[{"id": "fake_id", "name": "Berserk Ygg Mock", "category_id": 2, "size": 524288000, "seed": 100, "leech": 10, "completed": 50, "age_stamp": 1700000000}]'
                elif "/torrent/" in url:
                    mock_response.headers = {"Content-Type": "application/x-bittorrent"}
                    mock_response._content = mock_torrent_bytes
                else:
                    mock_response.status_code = 404
                return mock_response

            # La Cale API (la-cale.space)
            if "la-cale.space" in url:
                if "/api/external" in url:
                    mock_response._content = b'[{"infoHash": "fake_id", "title": "Berserk La Cale Mock", "category": "Animation", "size": 629145600, "seeders": 150, "leechers": 20, "pubDate": "2023-11-15T12:00:00Z"}]'
                elif "/api/torrents/download/" in url:
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
