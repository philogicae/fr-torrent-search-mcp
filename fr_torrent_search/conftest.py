from unittest.mock import patch

import pytest
import requests


@pytest.fixture(autouse=True, scope="session")
def mock_env(monkeypatch_session):
    """Set up environment variables for testing."""
    monkeypatch_session.setenv("LA_CALE_PASSKEY", "mock_passkey")
    monkeypatch_session.setenv("YGG_BASE_URL", "http://localhost:8715")


@pytest.fixture(autouse=True)
def mock_torrent_apis():
    """Mock YGG and La Cale API responses for local testing."""
    with patch("requests.Session.request") as mock_request:

        def side_effect(method, url, **kwargs):
            mock_response = requests.Response()
            mock_response.status_code = 200
            mock_response.headers = {"Content-Type": "application/json"}

            # YGG API (localhost:8715 or specific IP)
            if ":8715" in url:
                if url.endswith("/status"):
                    mock_response._content = b'{"status": "ok"}'
                elif url.endswith("/categories"):
                    mock_response._content = b'[{"id": 1, "name": "Film", "sub_categories": [{"id": 2, "name": "Animation"}]}, {"id": 3, "name": "S\xc3\xa9rie"}]'
                elif "/search" in url:
                    mock_response._content = b'[{"id": "1268760", "name": "Berserk Ygg Mock", "category_id": 2, "size": 524288000, "seed": 100, "leech": 10, "completed": 50, "age_stamp": 1700000000}]'
                elif "/torrent/" in url:
                    # Return magnet link for YGG via 302 redirect
                    mock_response.status_code = 302
                    mock_response.headers = {
                        "Location": "magnet:?xt=urn:btih:mock_hash&dn=Berserk+Mock"
                    }
                    mock_response._content = b""
                else:
                    mock_response.status_code = 404
                return mock_response

            # La Cale API (la-cale.space)
            if "la-cale.space" in url:
                if "/api/external" in url:
                    mock_response._content = b'[{"infoHash": "81d31b94f868658ea44d3ef6bfd28de2ec9ea63c", "title": "Berserk La Cale Mock", "category": "Animation", "size": 629145600, "seeders": 150, "leechers": 20, "pubDate": "2023-11-15T12:00:00Z"}]'
                elif "/api/torrents/download/" in url:
                    mock_response.headers = {"Content-Type": "application/x-bittorrent"}
                    mock_response._content = (
                        b"d4:infod4:name12:Berserk Mock6:lengthi629145600eee"
                    )
                else:
                    mock_response.status_code = 404
                return mock_response

            # Fallback for other requests
            mock_response.status_code = 404
            return mock_response

        mock_request.side_effect = side_effect
        yield mock_request


@pytest.fixture(scope="session")
def monkeypatch_session():
    """Session-scoped monkeypatch."""
    from _pytest.monkeypatch import MonkeyPatch

    m = MonkeyPatch()
    yield m
    m.undo()
