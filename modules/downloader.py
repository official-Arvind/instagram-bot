"""
modules/downloader.py
Download videos and images from Instagram URLs with retry logic.
Generates thumbnails using ffmpeg.
"""

import os
import time
import subprocess
from pathlib import Path
from rich.console import Console
import requests
from PIL import Image

console = Console()

DOWNLOADS_DIR = Path(__file__).parent.parent / "downloads"
DOWNLOADS_DIR.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def _download_url(url: str, dest: Path, retries: int = 3) -> bool:
    """Download a URL to dest. Returns True on success."""
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, headers=HEADERS, stream=True, timeout=30)
            r.raise_for_status()
            with open(dest, 'wb') as f:
                for chunk in r.iter_content(chunk_size=16384):
                    f.write(chunk)
            return True
        except Exception as e:
            console.print(f"    [yellow]Download attempt {attempt}/{retries} failed: {e}[/yellow]")
            if attempt < retries:
                time.sleep(2 ** attempt)
    return False


def _generate_thumbnail_ffmpeg(video_path: Path, thumb_path: Path) -> bool:
    """Generate JPEG thumbnail from video using ffmpeg. Returns True on success."""
    cmd = [
        "ffmpeg", "-y", "-ss", "1", "-i", str(video_path),
        "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
        "-vframes", "1",
        "-q:v", "2",
        str(thumb_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


def _convert_thumbnail(src: Path, dest: Path) -> bool:
    """Convert any image format (webp, png, etc.) to JPEG."""
    try:
        with Image.open(src) as im:
            rgb_im = im.convert("RGB")
            rgb_im.save(dest, "JPEG", quality=90)
        return True
    except Exception as e:
        console.print(f"    [yellow]Thumbnail convert failed: {e}[/yellow]")
        return False


def download_media(media: dict, slot: str) -> tuple[Path | None, Path | None]:
    """
    Download a media item (video + thumbnail or just image).
    
    Args:
        media: Dict from scout (contains video_url, thumbnail_url, media_type)
        slot:  Unique name for temp files (e.g. "item_1")
    
    Returns:
        (media_path, thumb_path) — both are local Path objects, or (None, None) on failure
    """
    base = DOWNLOADS_DIR / slot
    video_path = base.with_suffix(".mp4")
    thumb_webp  = base.with_name(slot + "_thumb.webp")
    thumb_jpg   = base.with_name(slot + "_thumb.jpg")

    # Clean up any leftover files
    for p in [video_path, thumb_webp, thumb_jpg]:
        if p.exists():
            p.unlink()

    if media["media_type"] == 2:  # Video
        if not media.get("video_url"):
            console.print("    [red]No video URL available.[/red]")
            return None, None

        console.print(f"    [dim]Downloading video...[/dim]")
        if not _download_url(media["video_url"], video_path):
            console.print("    [red]Video download failed.[/red]")
            return None, None

        # Try ffmpeg first, fall back to thumbnail URL
        console.print(f"    [dim]Generating thumbnail...[/dim]")
        thumb_ok = _generate_thumbnail_ffmpeg(video_path, thumb_jpg)
        if not thumb_ok:
            if media.get("thumbnail_url"):
                _download_url(media["thumbnail_url"], thumb_webp)
                thumb_ok = _convert_thumbnail(thumb_webp, thumb_jpg)

        thumb_path = thumb_jpg if thumb_ok and thumb_jpg.exists() else None
        return video_path, thumb_path

    else:  # Photo
        if not media.get("thumbnail_url"):
            console.print("    [red]No image URL available.[/red]")
            return None, None

        console.print(f"    [dim]Downloading image...[/dim]")
        if not _download_url(media["thumbnail_url"], thumb_webp):
            console.print("    [red]Image download failed.[/red]")
            return None, None

        # Convert to JPG
        img_jpg = base.with_suffix(".jpg")
        if not _convert_thumbnail(thumb_webp, img_jpg):
            return None, None

        return img_jpg, img_jpg  # For photos, both paths point to the image


def cleanup(paths: list[Path]):
    """Delete temp files after upload."""
    for p in paths:
        try:
            if p and p.exists():
                p.unlink()
        except Exception:
            pass
