"""
modules/caption.py
Smart caption processing and @-tag replacement.
"""

import re


# Lines to always preserve (don't modify)
_PRESERVE_PATTERNS = [
    r'video\s+courtesy',
    r'credit\s+goes\s+to',
    r'all\s+credit',
    r'dm\s+for\s+(removal|credit)',
    r'poet\s*[-:]',
    r'poetry\s+by',
    r'#\w+',  # hashtag-only lines
]

_FOLLOW_PATTERNS = [
    # "Follow @handle" / "Follow - @handle" / "Follow me @handle" / "Follow us @handle"
    re.compile(
        r'(?i)(follow(?:\s+(?:me|us|for\s+more|more))?\s*[-–]?\s*@?)[\w.]+'
    ),
    # Multiple @-tags after a "follow" word: "follow @a @b @c"
    re.compile(
        r'(?i)(follow[^@\n]*@)[\w.]+(?:\s*@[\w.]+)*'
    ),
]

_SPAM_LINE = re.compile(r'^(\s*@[\w.]+\s*){3,}$')  # Line with 3+ @tags only
_MULTI_SAME_HANDLE = re.compile(r'(@[\w.]+)(?:\s+\1){2,}', re.IGNORECASE)  # same @handle 2+ times


def _is_spam_line(line: str) -> bool:
    """Check if a line is pure @-tag spam."""
    stripped = line.strip()
    if not stripped:
        return False
    # All tokens are @handles
    tokens = stripped.split()
    handles = [t for t in tokens if t.startswith('@')]
    if len(tokens) > 0 and len(handles) == len(tokens) and len(handles) >= 3:
        return True
    # Same handle repeated 3+ times
    all_handles = re.findall(r'@[\w.]+', stripped)
    if len(all_handles) >= 3:
        unique = set(h.lower() for h in all_handles)
        if len(unique) <= 2:
            return True
    return False


def smart_replace(caption: str, logged_in_username: str, tags: list[str] = None) -> str:
    """
    Process a caption intelligently:
    - Replace 'follow @xxx' patterns with logged-in username
    - Remove spam @-tag lines
    - Remove duplicate same-handle repetitions
    - Ensure our account handle appears in the caption
    """
    if not caption:
        tags_list = tags if tags else ["explore", "viral", "instagram"]
        hashtag_str = " ".join(f"#{t.lower()}" for t in tags_list)
        return f"Follow @{logged_in_username} for more!\n\n{hashtag_str}"

    lines = caption.split('\n')
    cleaned_lines = []

    for line in lines:
        # Skip spam-only @-tag lines
        if _is_spam_line(line):
            continue

        # Remove repeated same-handle occurrences: "@a @a @a" → "@a"
        line = _MULTI_SAME_HANDLE.sub(r'\1', line)

        # Apply follow-replacement patterns
        for pattern in _FOLLOW_PATTERNS:
            line = pattern.sub(
                lambda m, u=logged_in_username: m.group(1) + u,
                line
            )

        cleaned_lines.append(line)

    result = '\n'.join(cleaned_lines).strip()

    # Remove excessive blank lines (3+ → 2)
    result = re.sub(r'\n{3,}', '\n\n', result)

    # Ensure our handle appears somewhere
    if f'@{logged_in_username}'.lower() not in result.lower():
        result += f'\n\nFollow @{logged_in_username} for more!'

    return result


def preview(caption: str, max_chars: int = 120) -> str:
    """Return a short preview of the caption for display in tables."""
    if not caption:
        return "[dim](no caption)[/dim]"
    # Take first non-empty lines
    lines = [l.strip() for l in caption.split('\n') if l.strip() and not l.strip().startswith('#')]
    text = ' • '.join(lines[:2])
    if len(text) > max_chars:
        text = text[:max_chars] + '...'
    return text
