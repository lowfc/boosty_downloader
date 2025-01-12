from pathlib import Path
from typing import Any
from core import logger
from mutagen.mp4 import MP4, MP4Cover
import aiohttp

def parse_metadata(post: dict[str, Any], media: dict[str, Any]) -> dict[str, Any]:
    return dict(
        title=post["title"],
        cover=media["preview"],
    )

async def empty_meta(_, __):
    return None

async def write_metadata(file_path: Path, metadata: dict[str, Any] | None):
    """
    Write metadata to MP4 file

    Parameters:
    file_path (str): Path to the MP4 file
    metadata (dict): Dictionary containing metadata fields
    """

    if not metadata:
        return

    try:
        # Open the MP4 file
        video = MP4(file_path)

        # Common metadata tags for MP4 files
        if "title" in metadata:
            video["\xa9nam"] = metadata["title"]


        if "description" in metadata:
            video["desc"] = metadata["description"]

        # Add cover art if provided
        if "cover" in metadata:
            async with aiohttp.ClientSession() as conn:
                resp = await conn.get(metadata["cover"])
                video['covr'] = [MP4Cover(await resp.read(), imageformat=MP4Cover.FORMAT_JPEG)]


        # Save the changes
        video.save()

    except Exception:
        logger.exception("Error writing metadata")

