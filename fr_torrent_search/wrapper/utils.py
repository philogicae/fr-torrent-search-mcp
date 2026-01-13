from base64 import b32encode
from datetime import datetime
from hashlib import sha1
from math import floor, log
from math import pow as pw
from os import getenv, makedirs
from pathlib import Path
from urllib import parse

from bencodepy import decode, encode
from dotenv import load_dotenv

load_dotenv()


def get_env(key: str, default: str | None = None) -> str | None:
    """Get environment variable with default value."""
    return getenv(key) or default


def get_env_bool(key: str, default: str | None = None) -> bool:
    """Get environment variable as boolean with default value."""
    value = get_env(key, default)
    if value is None:
        return True
    return value.lower() not in ("0", "false")


def ensure_folder(folder: str | Path | None) -> str | Path | None:
    """Ensure a folder exists, creating it if necessary."""
    if folder:
        makedirs(folder, exist_ok=True)
        return folder
    return None


def get_folder_torrent_files() -> Path:
    """Get the torrent files folder path, creating it if necessary."""
    folder = Path(str(get_env("FOLDER_TORRENT_FILES", "./torrents")))
    ensure_folder(folder)
    return folder


def format_size(size_bytes: int | None) -> str:
    """Converts a size in bytes to a human-readable string."""
    if size_bytes is None:
        return "N/A"
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(floor(log(size_bytes, 1024)))
    p = pw(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"


def format_date(field: str | int | None) -> str:
    """Converts an ISO date or a timestamp to a human-readable string 'YYYY-MM-DD HH:MM:SS' or 'N/A' if input is None."""
    try:
        if isinstance(field, int):
            return datetime.fromtimestamp(field).strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(field, str):
            return datetime.fromisoformat(field).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        pass
    return "N/A"


def torrent_bytes_to_magnet(
    torrent_bytes: bytes, trackers: str | list[str] | None = None
) -> str:
    """Converts a torrent file to a magnet link."""
    metadata = decode(torrent_bytes)
    announce = metadata[b"announce"]  # type: ignore
    subj = metadata[b"info"]  # type: ignore
    hashcontents = encode(subj)
    digest = sha1(hashcontents).digest()
    b32hash = b32encode(digest).decode()

    total_length = (
        sum(f[b"length"] for f in subj[b"files"])
        if b"files" in subj
        else subj[b"length"]
    )

    trs: list[str] = []
    if isinstance(trackers, str):
        trs = [parse.quote(trackers)]
    elif isinstance(trackers, list):
        trs = [parse.quote(tracker) for tracker in trackers]
    else:
        trs = [parse.quote(announce.decode())]

    return (
        f"magnet:?xt=urn:btih:{b32hash}"
        + f"&dn={parse.quote(subj[b'name'].decode())}"
        + f"&xl={total_length}&tr="
        + "&tr=".join(trs)
    )
