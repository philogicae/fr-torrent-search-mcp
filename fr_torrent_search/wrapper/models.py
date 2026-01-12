from enum import Enum

from pydantic import BaseModel


class Mode(Enum):
    FILE = "file"
    MAGNET = "magnet"
    BYTES = "bytes"


class Torrent(BaseModel):
    id: str
    filename: str
    category: str
    size: str
    seeders: int
    leechers: int
    downloads: int | str | None = None
    date: str
    magnet_link: str | None = None
    source: str

    def __str__(self) -> str:
        return str(self.model_dump(exclude_unset=True, exclude_none=True))
