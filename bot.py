"""
Instagram Bot — Master CLI
===========================================
Autonomous Instagram content bot powered by instagrapi.
Find, scout, filter, download, caption-edit, and post
viral content — all from a single interactive terminal.

Usage:
    python bot.py
"""

import sys
import time
import re
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.columns import Columns
from rich.text import Text
from rich import box
from rich.rule import Rule

from modules import auth, scout, caption, downloader, uploader

console = Console()

# ─────────────────────────────────────────────────────
BANNER = r"""
[bold magenta]
  ██╗███╗   ██╗███████╗████████╗ █████╗ [bold white] ██████╗  ██████╗ ████████╗
  ██║████╗  ██║██╔════╝╚══██╔══╝██╔══██╗[bold white]██╔══██╗██╔═══██╗╚══██╔══╝
  ██║██╔██╗ ██║███████╗   ██║   ███████║[bold white]██████╔╝██║   ██║   ██║   
  ██║██║╚██╗██║╚════██║   ██║   ██╔══██║[bold white]██╔══██╗██║   ██║   ██║   
  ██║██║ ╚████║███████║   ██║   ██║  ██║[bold white]██████╔╝╚██████╔╝   ██║   
  ╚═╝╚═╝  ╚═══╝╚══════╝   ╚═╝   ╚═╝  ╚═╝[bold white]╚═════╝  ╚═════╝    ╚═╝   
[/bold magenta]"""

CONTENT_TYPES = {
    "1": ("reel",       "🎬  Reels"),
    "2": ("story",      "📖  Stories"),
    "3": ("photo",      "🖼️   Photos"),
    "4": ("photomusic", "🎵  Photos with Music"),
}

# ─────────────────────────────────────────────────────

def show_banner():
    console.clear()
    console.print(BANNER)
    console.print(
        Panel(
            "[bold white]Autonomous Instagram Content Bot[/bold white]\n"
            "[dim]Scout  •  Download  •  Caption Edit  •  Post[/dim]",
            border_style="magenta",
            padding=(0, 4),
        )
    )
    console.print()


def get_hashtags() -> list[str]:
    console.print(Rule("[bold cyan]Step 1 — Hashtags[/bold cyan]", style="cyan"))
    console.print("[dim]Enter hashtags separated by commas. No # needed.[/dim]")
    raw = Prompt.ask("\n  [bold cyan]Hashtags[/bold cyan]")
    tags = list(dict.fromkeys([t.strip().lstrip('#').strip() for t in raw.split(',') if t.strip()]))
    if not tags:
        console.print("[red]Please enter at least one hashtag.[/red]")
        return get_hashtags()
    console.print(f"\n  [dim]Searching:[/dim] " + "  ".join(f"[cyan]#{t}[/cyan]" for t in tags))
    return tags


def get_content_type() -> str:
    console.print()
    console.print(Rule("[bold cyan]Step 2 — Content Type[/bold cyan]", style="cyan"))
    for k, (_, label) in CONTENT_TYPES.items():
        console.print(f"  [bold cyan][{k}][/bold cyan]  {label}")

    choice = Prompt.ask("\n  [bold]Select[/bold]", choices=list(CONTENT_TYPES.keys()), default="1")
    ctype, label = CONTENT_TYPES[choice]
    console.print(f"\n  [dim]Type selected:[/dim] [bold]{label}[/bold]")
    if ctype == "photomusic":
        console.print("  [yellow]⚠ Note: Music attachments are currently unsupported by instagrapi. Posting as standard Photo.[/yellow]")
    return ctype


def get_count() -> int:
    console.print()
    console.print(Rule("[bold cyan]Step 3 — How Many?[/bold cyan]", style="cyan"))
    console.print("[dim]How many pieces of content should the bot scout for you?[/dim]")
    count = IntPrompt.ask("\n  [bold cyan]Count[/bold cyan]", default=10)
    if count < 1:
        count = 1
    return count


def display_candidates(candidates: list[dict]) -> None:
    console.print()
    console.print(Rule("[bold green]Results[/bold green]", style="green"))

    table = Table(
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta",
        border_style="dim",
        padding=(0, 1),
    )
    table.add_column("#",        style="bold white",  width=3,  no_wrap=True)
    table.add_column("Author (Ctrl+Click to view)", style="cyan", width=22, no_wrap=True)
    table.add_column("👁 Views",  style="green",       width=10, no_wrap=True, justify="right")
    table.add_column("❤ Likes",  style="red",         width=10, no_wrap=True, justify="right")
    table.add_column("⏱ Dur",    style="yellow",      width=6,  no_wrap=True, justify="right")
    table.add_column("Caption Preview",               min_width=20)

    for i, c in enumerate(candidates, 1):
        dur = f"{c['duration']:.0f}s" if c.get("duration") else "—"
        views = f"{c['views']:,}" if c.get("views") else "—"
        likes = f"{c['likes']:,}" if c.get("likes") else "—"
        cap_prev = caption.preview(c.get("caption", ""))
        
        # Create clickable terminal hyperlink to the post URL
        author_text = Text.from_markup(f"[link={c['url']}]@{c['author']}[/link]", style="cyan")
        
        table.add_row(str(i), author_text, views, likes, dur, cap_prev)

    console.print(table)
    console.print(f"\n  [dim]Total found: {len(candidates)} results[/dim]")


def parse_selection(raw: str, max_n: int) -> list[int]:
    """
    Parse user selection string into list of 0-based indices.
    Supports: "all", "1,3,5", "1-3", "2,4-6,8"
    """
    raw = raw.strip().lower()
    if raw == "all":
        return list(range(max_n))

    indices = set()
    for part in raw.split(','):
        part = part.strip()
        if '-' in part:
            a, _, b = part.partition('-')
            try:
                for x in range(int(a), int(b) + 1):
                    if 1 <= x <= max_n:
                        indices.add(x - 1)
            except ValueError:
                pass
        else:
            try:
                x = int(part)
                if 1 <= x <= max_n:
                    indices.add(x - 1)
            except ValueError:
                pass

    return sorted(indices)


def get_selection(candidates: list[dict]) -> list[dict]:
    console.print()
    console.print(Rule("[bold cyan]Step 4 — Select Content[/bold cyan]", style="cyan"))
    console.print(
        "[dim]Enter numbers to post. Examples:[/dim]\n"
        "  [cyan]1,3,5[/cyan]   → post items 1, 3 and 5\n"
        "  [cyan]1-4[/cyan]     → post items 1 through 4\n"
        "  [cyan]all[/cyan]     → post everything\n"
    )

    raw = Prompt.ask("\n  [bold cyan]Your selection[/bold cyan]")
    indices = parse_selection(raw, len(candidates))

    if not indices:
        console.print("[red]Invalid selection. Try again.[/red]")
        return get_selection(candidates)

    selected = [candidates[i] for i in indices]
    console.print(f"\n  [bold green]✓ Selected {len(selected)} item(s):[/bold green] " +
                  ", ".join(f"[cyan]#{i+1}[/cyan]" for i in indices))
    return selected


def process_and_post(cl, username: str, items: list[dict], content_type: str, hashtags: list[str] = None) -> list[dict]:
    """Download, edit captions, and upload all selected items."""
    console.print()
    console.print(Rule("[bold magenta]Posting...[/bold magenta]", style="magenta"))

    results = []

    for idx, item in enumerate(items, 1):
        console.print(f"\n  [bold white][{idx}/{len(items)}][/bold white] "
                      f"@{item['author']} — {item['url']}")

        # Download
        slot = f"item_{idx}_{int(time.time())}"
        vid_path, thumb_path = downloader.download_media(item, slot)

        if vid_path is None and thumb_path is None:
            console.print("    [red]⚠ Skipping — download failed.[/red]")
            results.append({"error": "download_failed", "url": item["url"]})
            continue

        # Edit caption
        raw_caption = item.get("caption", "")
        new_caption = caption.smart_replace(raw_caption, username, hashtags)

        # Upload
        result = uploader.post(cl, content_type, vid_path, thumb_path, new_caption)

        # Cleanup temp files
        files_to_clean = [f for f in [vid_path, thumb_path] if f]
        # Also clean webp companion
        if vid_path:
            webp = vid_path.parent / (vid_path.stem + "_thumb.webp")
            files_to_clean.append(webp)
        downloader.cleanup(files_to_clean)

        if result:
            console.print(f"    [bold green]✅ Posted![/bold green] {result['url']}")
            result["original_url"] = item["url"]
            result["author"] = item["author"]
            results.append(result)
        else:
            console.print(f"    [red]❌ Upload failed.[/red]")
            results.append({"error": "upload_failed", "url": item["url"]})

    return results


def show_summary(results: list[dict]):
    console.print()
    console.print(Rule("[bold green]Summary[/bold green]", style="green"))

    success = [r for r in results if "url" in r and "error" not in r]
    failed  = [r for r in results if "error" in r]

    console.print(f"\n  [bold green]✅ {len(success)} posted successfully[/bold green]"
                  + (f"   [red]❌ {len(failed)} failed[/red]" if failed else ""))

    if success:
        table = Table(box=box.SIMPLE, header_style="bold", border_style="dim")
        table.add_column("Type",   style="cyan",  width=10)
        table.add_column("Source", style="dim",   width=25)
        table.add_column("Posted URL", style="bold green")

        for r in success:
            table.add_row(
                r.get("type", "—"),
                f"@{r.get('author', '?')}",
                r.get("url", "—"),
            )
        console.print(table)


# ─────────────────────────────────────────────────────
def main():
    show_banner()

    # ── Login ──
    console.print(Rule("[bold cyan]Login[/bold cyan]", style="cyan"))
    cl, username = auth.login_flow()
    console.print(f"\n  [bold green]✓ Ready to post as @{username}[/bold green]\n")

    # ── Main loop ──
    while True:
        # Gather inputs
        hashtags     = get_hashtags()
        content_type = get_content_type()
        count        = get_count()

        # Scout
        console.print()
        console.print(Rule("[bold cyan]Step 4 — Scouting Content[/bold cyan]", style="cyan"))
        console.print(f"  [dim]Fetching top [bold]{count}[/bold] {content_type}s across {len(hashtags)} hashtag(s)...[/dim]\n")

        candidates = scout.search_content(cl, hashtags, content_type, count)

        if not candidates:
            console.print("\n  [yellow]⚠ No content found for those hashtags/type. Try different hashtags.[/yellow]")
        else:
            # Display & select
            display_candidates(candidates)
            selected = get_selection(candidates)

            # Confirm
            console.print()
            if Confirm.ask(f"  [bold]Post {len(selected)} item(s) to @{username}?[/bold]", default=True):
                results = process_and_post(cl, username, selected, content_type, hashtags)
                show_summary(results)
            else:
                console.print("  [yellow]Cancelled.[/yellow]")

        # Continue?
        console.print()
        if not Confirm.ask("[bold]Post more content?[/bold]", default=True):
            break

    # ── Exit ──
    console.print()
    console.print(Panel(
        f"[bold green]Session saved. See you soon! 👋[/bold green]\n"
        f"[dim]Account: @{username}[/dim]",
        border_style="green",
        padding=(0, 4),
    ))
    console.print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n  [yellow]Interrupted. Goodbye![/yellow]\n")
        sys.exit(0)
