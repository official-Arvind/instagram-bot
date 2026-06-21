"""
modules/auth.py
Login and session management for Instagram Bot.
Supports: username/password, session file, session cookie.
"""

import os
import json
import glob
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, IntPrompt
from rich import print as rprint
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, TwoFactorRequired, ChallengeRequired

console = Console()
SESSIONS_DIR = Path(__file__).parent.parent / "sessions"
SESSIONS_DIR.mkdir(exist_ok=True)


def _session_path(username: str) -> Path:
    return SESSIONS_DIR / f"{username}.json"


def _list_saved_sessions() -> list[Path]:
    return sorted(SESSIONS_DIR.glob("*.json"))


def _try_resume_session(cl: Client, path: Path) -> bool:
    """Try to resume an existing session. Returns True on success."""
    try:
        cl.load_settings(str(path))
        cl.get_timeline_feed()  # Lightweight check
        return True
    except Exception:
        return False


def _save_session(cl: Client, username: str):
    path = _session_path(username)
    cl.dump_settings(str(path))
    console.print(f"  [dim]Session saved → sessions/{username}.json[/dim]")


def _login_username_password(cl: Client) -> tuple[str, bool]:
    """Login with username and password. Returns (username, success)."""
    console.print("\n[bold]Enter your Instagram credentials:[/bold]")
    username = Prompt.ask("  [cyan]Username[/cyan]")
    password = Prompt.ask("  [cyan]Password[/cyan]", password=True)

    try:
        console.print("  [dim]Logging in...[/dim]")
        cl.login(username, password)
        return username, True
    except TwoFactorRequired:
        console.print("  [yellow]2FA required.[/yellow]")
        code = Prompt.ask("  Enter 2FA code")
        try:
            cl.login(username, password, verification_code=code)
            return username, True
        except Exception as e:
            console.print(f"  [red]2FA login failed: {e}[/red]")
            return username, False
    except ChallengeRequired:
        console.print("  [yellow]Instagram sent a challenge (check your email/phone).[/yellow]")
        try:
            cl.challenge_resolve(cl.last_json)
            code = Prompt.ask("  Enter challenge code")
            cl.challenge_resolve(cl.last_json, code)
            return username, True
        except Exception as e:
            console.print(f"  [red]Challenge failed: {e}[/red]")
            return username, False
    except Exception as e:
        console.print(f"  [red]Login failed: {e}[/red]")
        return username, False


def _login_session_file(cl: Client) -> tuple[str, bool]:
    """Load a session JSON file. Returns (username, success)."""
    file_path = Prompt.ask("  [cyan]Path to session JSON file[/cyan]")
    file_path = file_path.strip('"').strip("'")
    if not os.path.exists(file_path):
        console.print(f"  [red]File not found: {file_path}[/red]")
        return "", False
    try:
        cl.load_settings(file_path)
        cl.get_timeline_feed()
        username = cl.username
        return username, True
    except Exception as e:
        console.print(f"  [red]Session file failed: {e}[/red]")
        return "", False


def _login_session_cookie(cl: Client) -> tuple[str, bool]:
    """Login with sessionid cookie. Returns (username, success)."""
    console.print("\n[bold]Session Cookie Login:[/bold]")
    console.print("  [dim]Go to Instagram.com → F12 → Application → Cookies → copy 'sessionid' value[/dim]")
    session_id = Prompt.ask("  [cyan]sessionid value[/cyan]")
    username = Prompt.ask("  [cyan]Your Instagram username[/cyan]")
    try:
        cl.login_by_sessionid(session_id)
        return username, True
    except Exception as e:
        console.print(f"  [red]Cookie login failed: {e}[/red]")
        return "", False


def login_flow() -> tuple[Client, str]:
    """
    Full login flow. Returns (Client, logged_in_username).
    Checks saved sessions first, then prompts for login method.
    """
    cl = Client()
    cl.delay_range = [1, 3]  # Be polite with the API

    # Check saved sessions
    saved = _list_saved_sessions()
    if saved:
        console.print("\n[bold green]Saved sessions found:[/bold green]")
        table = Table(show_header=True, header_style="bold magenta", box=None)
        table.add_column("#", style="dim", width=4)
        table.add_column("Account", style="cyan")
        for i, s in enumerate(saved, 1):
            table.add_row(str(i), s.stem)
        console.print(table)
        console.print(f"  [{len(saved)+1}] Login with a new account\n")

        choice = Prompt.ask(
            "  [bold]Select[/bold]",
            choices=[str(i) for i in range(1, len(saved) + 2)],
            default="1"
        )
        idx = int(choice) - 1

        if idx < len(saved):
            path = saved[idx]
            console.print(f"  [dim]Resuming session for [cyan]{path.stem}[/cyan]...[/dim]")
            if _try_resume_session(cl, path):
                console.print(f"  [bold green]✓ Logged in as @{path.stem}[/bold green]")
                return cl, path.stem
            else:
                console.print("  [yellow]Session expired. Please login again.[/yellow]")

    # Fresh login
    console.print("\n[bold]How would you like to login?[/bold]")
    console.print("  [bold cyan][1][/bold cyan] Username + Password")
    console.print("  [bold cyan][2][/bold cyan] Load session JSON file")
    console.print("  [bold cyan][3][/bold cyan] Session Cookie (sessionid)")

    method = Prompt.ask("\n  [bold]Choice[/bold]", choices=["1", "2", "3"], default="1")

    username, success = "", False
    if method == "1":
        username, success = _login_username_password(cl)
    elif method == "2":
        username, success = _login_session_file(cl)
    elif method == "3":
        username, success = _login_session_cookie(cl)

    if not success:
        console.print("\n[bold red]Login failed. Please try again.[/bold red]")
        return login_flow()  # Retry

    _save_session(cl, username)
    console.print(f"\n  [bold green]✓ Logged in as @{username}[/bold green]")
    return cl, username
