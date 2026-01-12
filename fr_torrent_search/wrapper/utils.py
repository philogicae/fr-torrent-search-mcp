from base64 import b32encode
from datetime import datetime
from hashlib import sha1
from math import floor, log
from math import pow as pw
from urllib import parse

from bencodepy import decode, encode


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


def torrent_bytes_to_magnet(torrent_bytes: bytes, trackers: str | list[str]) -> str:
    """Converts a torrent file to a magnet link."""
    metadata = decode(torrent_bytes)
    subj = metadata[b"info"]  # type: ignore
    hashcontents = encode(subj)
    digest = sha1(hashcontents).digest()
    b32hash = b32encode(digest).decode()

    if b"files" in subj:
        total_length = sum(f[b"length"] for f in subj[b"files"])
    else:
        total_length = subj[b"length"]
    return (
        "magnet:?xt=urn:btih:"
        + b32hash
        + "&dn="
        + parse.quote(subj[b"name"].decode())
        + "&tr="
        + "&tr=".join(
            parse.quote(tracker)
            for tracker in (trackers if isinstance(trackers, list) else [trackers])
        )
        + "&xl="
        + str(total_length)
    )
