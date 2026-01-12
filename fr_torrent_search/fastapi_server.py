import shutil
import tempfile
from pathlib import Path as PathLibPath

from fastapi import FastAPI, HTTPException, Path
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from .wrapper import FrTorrentApi, Torrent

app = FastAPI(
    title="Fr Torrent Search FastAPI",
    description="FastAPI server for searching torrents across multiple providers.",
)


client = FrTorrentApi()
client.ensure_initialized()


def cleanup_temp_dir(dir_path: str) -> None:
    """Safely removes a directory and its contents."""
    try:
        shutil.rmtree(dir_path)
    except OSError as e:
        print(f"Error removing temporary directory {dir_path}: {e}")


# --- API Endpoints ---
@app.get("/", summary="Health Check", tags=["General"], response_model=dict[str, str])
async def health_check() -> dict[str, str]:
    """
    Endpoint to check the health of the service.
    """
    return {"status": "ok"}


@app.post(
    "/torrent/search",
    summary="Search Torrents",
    tags=["Torrents"],
    response_model=list[Torrent],
)
async def search_torrents(
    query: str,
    max_items: int = 10,
) -> list[Torrent]:
    """
    Search for torrents across multiple providers.
    Corresponds to `FrTorrentApi.search_torrents()`.
    """
    return client.search_torrents(query=query, max_items=max_items)


@app.get(
    "/torrent/{torrent_id}",
    summary="Get Torrent",
    tags=["Torrents"],
)
async def get_torrent(
    torrent_id: str = Path(..., description="The ID of the torrent."),
):
    """
    Get a specific torrent (either magnet link, torrent file content, or torrent file path).
    Corresponds to `FrTorrentApi.get_torrent()`.
    """
    temp_dir_path = tempfile.mkdtemp()
    try:
        result = client.get_torrent(torrent_id, output_dir=temp_dir_path)
        if not result:
            cleanup_temp_dir(temp_dir_path)
            raise HTTPException(
                status_code=404, detail="Torrent not found or could not be retrieved."
            )

        # Handle bytes (torrent file content)
        if isinstance(result, bytes):
            filename = f"{torrent_id}.torrent"
            full_file_path = PathLibPath(temp_dir_path) / filename
            with open(full_file_path, "wb") as f:
                f.write(result)

            return FileResponse(
                path=str(full_file_path),
                media_type="application/x-bittorrent",
                filename=filename,
                background=BackgroundTask(cleanup_temp_dir, temp_dir_path),
            )

        # Handle string (magnet link or filename)
        if isinstance(result, str):
            if result.startswith("magnet:"):
                cleanup_temp_dir(temp_dir_path)
                return result

            # Check if it's a filename or path
            file_path = PathLibPath(result)
            if not file_path.is_absolute():
                file_path = PathLibPath(temp_dir_path) / result

            if file_path.is_file():
                return FileResponse(
                    path=str(file_path),
                    media_type="application/x-bittorrent",
                    filename=file_path.name,
                    background=BackgroundTask(cleanup_temp_dir, temp_dir_path),
                )

            # If it's a string but not magnet/file, just return it
            cleanup_temp_dir(temp_dir_path)
            return result

        # Fallback for any other successful result
        cleanup_temp_dir(temp_dir_path)
        return result

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        cleanup_temp_dir(temp_dir_path)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while retrieving the torrent: {str(e)}",
        ) from e


@app.get(
    "/torrent/{torrent_id}/magnet",
    summary="Get Magnet Link",
    tags=["Torrents"],
    response_model=str,
)
async def get_magnet_link(
    torrent_id: str = Path(..., description="The ID of the torrent."),
) -> str:
    """
    Get the magnet link for a specific torrent.
    Corresponds to `FrTorrentApi.get_magnet_link()`.
    """
    magnet_link = client.get_magnet_link(torrent_id)
    if not magnet_link:
        raise HTTPException(
            status_code=404, detail="Magnet link not found or could not be generated."
        )
    return magnet_link


@app.get(
    "/torrent/{torrent_id}/file",
    summary="Download .torrent File",
    tags=["Torrents"],
    response_class=FileResponse,
)
async def download_torrent_file(
    torrent_id: str = Path(..., description="The ID of the torrent."),
) -> FileResponse:
    """
    Download the .torrent file for a specific torrent.
    Corresponds to `FrTorrentApi.download_torrent_file()`.
    The file is downloaded to a temporary location on the server and then streamed.
    The temporary file is cleaned up afterwards.
    """
    temp_dir_path = None
    try:
        temp_dir_path = tempfile.mkdtemp()
        downloaded_filename = client.download_torrent_file(
            torrent_id=torrent_id, output_dir=temp_dir_path
        )

        if not downloaded_filename:
            if temp_dir_path:
                cleanup_temp_dir(temp_dir_path)
            raise HTTPException(
                status_code=404, detail="Torrent file not found or download failed."
            )

        full_file_path = PathLibPath(temp_dir_path) / downloaded_filename
        if not full_file_path.is_file():
            if temp_dir_path:
                cleanup_temp_dir(temp_dir_path)
            raise HTTPException(
                status_code=500,
                detail="Torrent file was not saved correctly on server.",
            )

        return FileResponse(
            path=str(full_file_path),
            media_type="application/x-bittorrent",
            filename=downloaded_filename,
            background=BackgroundTask(cleanup_temp_dir, temp_dir_path),
        )
    except Exception as e:
        if temp_dir_path:
            cleanup_temp_dir(temp_dir_path)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing the torrent download: {str(e)}",
        ) from e
