"""
modules/uploader.py
Upload content to Instagram: Reels, Stories, Photos.
"""

import time
from pathlib import Path
from rich.console import Console

console = Console()


def upload_reel(cl, video_path: Path, thumb_path: Path | None, caption: str) -> dict | None:
    """Upload a Reel. Returns result dict with id and url, or None on failure."""
    try:
        console.print("    [dim]Uploading Reel...[/dim]")
        kwargs = {"caption": caption}
        if thumb_path and thumb_path.exists():
            kwargs["thumbnail"] = thumb_path

        media = cl.clip_upload(str(video_path), **kwargs)
        return {
            "type": "reel",
            "id": media.id,
            "code": media.code,
            "url": f"https://www.instagram.com/reel/{media.code}/",
        }
    except Exception as e:
        console.print(f"    [red]Reel upload failed: {e}[/red]")
        return None


def upload_story_video(cl, video_path: Path, thumb_path: Path | None) -> dict | None:
    """Upload a video Story. Returns result dict or None on failure."""
    try:
        console.print("    [dim]Uploading Story (video)...[/dim]")
        kwargs = {}
        if thumb_path and thumb_path.exists():
            kwargs["thumbnail"] = thumb_path

        media = cl.video_upload_to_story(str(video_path), **kwargs)
        return {
            "type": "story",
            "id": media.id,
            "url": f"https://www.instagram.com/stories/{cl.username}/{media.pk}/",
        }
    except Exception as e:
        console.print(f"    [red]Story upload failed: {e}[/red]")
        return None


def upload_story_photo(cl, image_path: Path) -> dict | None:
    """Upload a photo Story."""
    try:
        console.print("    [dim]Uploading Story (photo)...[/dim]")
        media = cl.photo_upload_to_story(str(image_path))
        return {
            "type": "story",
            "id": media.id,
            "url": f"https://www.instagram.com/stories/{cl.username}/{media.pk}/",
        }
    except Exception as e:
        console.print(f"    [red]Story photo upload failed: {e}[/red]")
        return None


def upload_photo(cl, image_path: Path, caption: str) -> dict | None:
    """Upload a photo post."""
    try:
        console.print("    [dim]Uploading Photo...[/dim]")
        media = cl.photo_upload(str(image_path), caption=caption)
        return {
            "type": "photo",
            "id": media.id,
            "code": media.code,
            "url": f"https://www.instagram.com/p/{media.code}/",
        }
    except Exception as e:
        console.print(f"    [red]Photo upload failed: {e}[/red]")
        return None


def post(cl, content_type: str, video_path: Path | None, thumb_path: Path | None, caption: str) -> dict | None:
    """
    Universal post function. Routes to the correct upload based on content_type.
    
    content_type: 'reel', 'story', 'photo', 'photomusic'
    """
    if content_type == "reel":
        return upload_reel(cl, video_path, thumb_path, caption)
    elif content_type == "story":
        if video_path and str(video_path).endswith(".mp4"):
            return upload_story_video(cl, video_path, thumb_path)
        else:
            return upload_story_photo(cl, thumb_path or video_path)
    elif content_type in ("photo", "photomusic"):
        img = thumb_path or video_path
        return upload_photo(cl, img, caption)
    else:
        console.print(f"    [red]Unknown content type: {content_type}[/red]")
        return None
