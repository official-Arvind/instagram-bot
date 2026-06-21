"""
modules/scout.py
Hashtag-based content discovery and ranking.
"""

import time
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

console = Console()

CONTENT_FILTERS = {
    "reel":   lambda m: m.media_type == 2 and getattr(m, 'product_type', '') == 'clips',
    "story":  lambda m: m.media_type in (1, 2),  # Both photos and videos can be posted as stories
    "photo":  lambda m: m.media_type == 1,
    "photomusic": lambda m: m.media_type == 1,
}


def _score(media) -> float:
    """Composite engagement score. Likes weighted more than views."""
    views = getattr(media, 'view_count', 0) or getattr(media, 'play_count', 0) or 0
    likes = getattr(media, 'like_count', 0) or 0
    return views * 0.3 + likes * 0.7


def _to_dict(media, cl) -> dict | None:
    """Convert instagrapi media object to a clean dict. Returns None on failure."""
    try:
        # Check if the media object already has the required details to avoid extra API calls
        has_details = False
        if media.media_type == 1:  # Photo
            has_details = bool(getattr(media, 'thumbnail_url', None))
        elif media.media_type == 2:  # Video
            has_details = bool(getattr(media, 'video_url', None))
        
        if has_details:
            fresh = media
        else:
            fresh = cl.media_info(media.pk)

        views = getattr(fresh, 'view_count', 0) or getattr(fresh, 'play_count', 0) or 0
        likes = getattr(fresh, 'like_count', 0) or 0
        duration = getattr(fresh, 'video_duration', 0) or 0
        caption = getattr(fresh, 'caption_text', '') or ''
        author = getattr(fresh.user, 'username', '') if getattr(fresh, 'user', None) else ''
        if not author and hasattr(fresh, 'username'):
            author = fresh.username

        return {
            "pk": int(fresh.pk),
            "id": fresh.id,
            "code": fresh.code,
            "url": f"https://www.instagram.com/reel/{fresh.code}/" if fresh.media_type == 2 else f"https://www.instagram.com/p/{fresh.code}/",
            "author": author,
            "views": views,
            "likes": likes,
            "duration": duration,
            "caption": caption,
            "video_url": str(getattr(fresh, 'video_url', '') or ''),
            "thumbnail_url": str(getattr(fresh, 'thumbnail_url', '') or ''),
            "media_type": fresh.media_type,
            "score": views * 0.3 + likes * 0.7,
        }
    except Exception:
        # Fallback to fetching full info on any error or missing fields
        try:
            fresh = cl.media_info(media.pk)
            views = getattr(fresh, 'view_count', 0) or getattr(fresh, 'play_count', 0) or 0
            likes = getattr(fresh, 'like_count', 0) or 0
            duration = getattr(fresh, 'video_duration', 0) or 0
            caption = getattr(fresh, 'caption_text', '') or ''
            return {
                "pk": int(fresh.pk),
                "id": fresh.id,
                "code": fresh.code,
                "url": f"https://www.instagram.com/reel/{fresh.code}/" if fresh.media_type == 2 else f"https://www.instagram.com/p/{fresh.code}/",
                "author": fresh.user.username,
                "views": views,
                "likes": likes,
                "duration": duration,
                "caption": caption,
                "video_url": str(getattr(fresh, 'video_url', '') or ''),
                "thumbnail_url": str(getattr(fresh, 'thumbnail_url', '') or ''),
                "media_type": fresh.media_type,
                "score": views * 0.3 + likes * 0.7,
            }
        except Exception:
            return None



def expand_hashtags(cl, base_tags: list[str], limit_per_tag: int = 2) -> list[str]:
    """
    Expand a list of base hashtags by searching Instagram for related trending hashtags.
    """
    expanded = list(base_tags)
    for tag in base_tags:
        try:
            # Query Instagram's search for similar hashtags
            results = cl.search_hashtags(tag)
            related = []
            for item in results:
                name = item.name.lower().strip()
                if name != tag.lower() and (tag.lower() in name or name in tag.lower()):
                    related.append((name, getattr(item, 'media_count', 0) or 0))
            
            # Sort by popularity (media count) descending
            related.sort(key=lambda x: x[1], reverse=True)
            
            # Take the top related tags
            added = 0
            for name, count in related:
                if name not in expanded:
                    expanded.append(name)
                    added += 1
                    if added >= limit_per_tag:
                        break
            time.sleep(0.2)  # Rate limit courtesy
        except Exception:
            pass
    return expanded


def search_content(cl, hashtags: list[str], content_type: str, target_count: int) -> list[dict]:
    """
    Search across multiple hashtags and return ranked list of content.
    
    Args:
        cl: Authenticated instagrapi Client
        hashtags: List of hashtags to search (without #)
        content_type: 'reel', 'story', 'photo', 'photomusic'
        target_count: How many results to return
    
    Returns:
        Sorted list of media dicts (most engaging first)
    """
    # Smart Hashtag Expansion
    console.print("  [dim]Expanding hashtags to discover related trending tags...[/dim]")
    expanded_tags = expand_hashtags(cl, hashtags)
    console.print("  [dim]Target tags:[/dim] " + "  ".join(f"[cyan]#{t}[/cyan]" for t in expanded_tags))
    console.print()

    content_filter = CONTENT_FILTERS.get(content_type, CONTENT_FILTERS["reel"])
    seen_pks = set()
    candidates = []
    fetch_per_tag = max(15, target_count * 2)  # Fetch extra to have margin

    with Progress(
        SpinnerColumn(spinner_name="dots"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("[cyan]Scouting hashtags...", total=len(expanded_tags))

        for tag in expanded_tags:
            progress.update(task, description=f"[cyan]Searching [bold]#{tag}[/bold]...")
            try:
                medias = cl.hashtag_medias_top(tag, amount=fetch_per_tag)
                for media in medias:
                    pk = int(media.pk)
                    if pk in seen_pks:
                        continue
                    if not content_filter(media):
                        continue
                    seen_pks.add(pk)

                    data = _to_dict(media, cl)
                    if data:
                        candidates.append(data)

                    time.sleep(0.3)  # Rate limit courtesy
            except Exception as e:
                console.print(f"  [yellow]⚠ #{tag}: {e}[/yellow]")

            progress.advance(task)

    # Sort by composite score
    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates[:target_count]
