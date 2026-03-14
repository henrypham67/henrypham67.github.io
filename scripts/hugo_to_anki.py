#!/usr/bin/env python3
"""
hugo_to_anki.py — Sync Anki flashcards from Hugo blog posts via AnkiConnect.

Usage:
    # Sync a single post (creates new cards, updates existing ones)
    python scripts/hugo_to_anki.py content/posts/linux/systemd.md

    # Sync all posts in a category
    python scripts/hugo_to_anki.py content/posts/linux/

    # Watch for changes and auto-sync
    python scripts/hugo_to_anki.py --watch content/posts/linux/systemd.md
    python scripts/hugo_to_anki.py --watch content/posts/

    # Dry run (preview without sending to Anki)
    python scripts/hugo_to_anki.py --dry-run content/posts/linux/systemd.md

Requirements:
    - Anki running with AnkiConnect plugin (code: 2055492159)
    - Python 3.8+

Card format in markdown:
    Add an `<!-- anki -->` block in your Hugo post:

    <!-- anki
    Q: What command enables a systemd service at boot?
    A: `systemctl enable <service>.service`
    tags: linux::systemd, commands

    Q: What are the three sections of a systemd unit file?
    A: [Unit], [Service], [Install]
    tags: linux::systemd, concepts

    cloze:
    tags: linux::systemd
    C: To enable a service at boot: `systemctl {{c1::enable}} ssh.service`
    C: The main sections are {{c1::[Unit]}}, {{c2::[Service]}}, {{c3::[Install]}}
    -->
"""

import argparse
import html
import json
import re
import sys
import time
import urllib.request
from pathlib import Path


ANKI_CONNECT_URL = "http://localhost:8765"
BLOG_BASE_URL = "https://henrypham67.github.io"


# ---------------------------------------------------------------------------
# AnkiConnect helpers
# ---------------------------------------------------------------------------

def anki_request(action: str, **params) -> dict:
    """Send a request to AnkiConnect API."""
    payload = json.dumps({"action": action, "version": 6, "params": params})
    req = urllib.request.Request(
        ANKI_CONNECT_URL,
        data=payload.encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
    except urllib.error.URLError:
        print("ERROR: Cannot connect to Anki. Is Anki running with AnkiConnect?")
        sys.exit(1)

    if result.get("error"):
        raise Exception(f"AnkiConnect error: {result['error']}")
    return result["result"]


def ensure_deck(deck_name: str):
    """Create deck if it doesn't exist."""
    anki_request("createDeck", deck=deck_name)


def find_notes(query: str) -> list[int]:
    """Find note IDs matching an AnkiConnect query."""
    return anki_request("findNotes", query=query)


def get_notes_info(note_ids: list[int]) -> list[dict]:
    """Get full info for a list of note IDs."""
    if not note_ids:
        return []
    return anki_request("notesInfo", notes=note_ids)


def update_note_fields(note_id: int, fields: dict):
    """Update fields on an existing note."""
    anki_request("updateNoteFields", note={"id": note_id, "fields": fields})


def replace_tags_on_note(note_id: int, old_tags: list[str], new_tags: list[str]):
    """Replace tags on a note using a diff: only remove stale, only add missing."""
    old_set = set(old_tags)
    new_set = set(new_tags)
    to_remove = old_set - new_set
    to_add = new_set - old_set
    if to_remove:
        anki_request("removeTags", notes=[note_id], tags=" ".join(to_remove))
    if to_add:
        anki_request("addTags", notes=[note_id], tags=" ".join(to_add))


def delete_notes(note_ids: list[int]):
    """Delete notes by IDs."""
    if note_ids:
        anki_request("deleteNotes", notes=note_ids)


def clear_unused_tags():
    """Remove all tags that are not used by any notes."""
    anki_request("clearUnusedTags")


# ---------------------------------------------------------------------------
# Hugo parsing
# ---------------------------------------------------------------------------

def parse_front_matter(content: str) -> dict:
    """Extract Hugo front matter (YAML between --- delimiters).

    Handles scalar values and inline JSON/YAML arrays, e.g.:
        tags: ["linux", "command", "systemd"]
        categories: ["DevOps", "Kubernetes"]
        title: 'Systemd'
    """
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return {}
    fm = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        key = key.strip().strip("'")
        val = val.strip()

        # Try parsing as JSON array: ["a", "b", "c"]
        if val.startswith("["):
            try:
                fm[key] = json.loads(val)
                continue
            except json.JSONDecodeError:
                pass

        fm[key] = val.strip("'\"")
    return fm


def derive_tags_from_path(filepath: Path) -> list[str]:
    """
    Derive Anki tags from the Hugo content path.

    content/posts/linux/systemd.md       -> ["blog", "linux", "linux::systemd"]
    content/posts/kubernetes/admin/etcd.md -> ["blog", "kubernetes", "kubernetes::admin"]
    """
    parts = filepath.parts
    try:
        posts_idx = parts.index("posts")
    except ValueError:
        return ["blog"]

    category_parts = list(parts[posts_idx + 1 : -1])  # exclude filename
    tags = ["blog"]
    if category_parts:
        tags.append(category_parts[0])  # e.g., "linux"
        if len(category_parts) > 1:
            tags.append("::".join(category_parts))  # e.g., "linux::admin"
        # Add topic tag from filename
        stem = filepath.stem  # e.g., "systemd"
        tags.append(f"{category_parts[0]}::{stem}")
    return tags


def derive_source_tag(filepath: Path) -> str:
    """Build a unique source tag to track which file a card came from.

    content/posts/linux/systemd.md -> "source::linux/systemd"
    """
    parts = filepath.parts
    try:
        posts_idx = parts.index("posts")
    except ValueError:
        return f"source::{filepath.stem}"
    rel_parts = parts[posts_idx + 1 :]
    rel = "/".join(rel_parts).replace(".md", "")
    return f"source::{rel}"


def derive_source_url(filepath: Path) -> str:
    """Build the blog URL from the file path."""
    parts = filepath.parts
    try:
        posts_idx = parts.index("posts")
    except ValueError:
        return BLOG_BASE_URL
    slug_parts = parts[posts_idx + 1 :]
    slug = "/".join(slug_parts)
    slug = slug.replace(".md", "/")
    return f"{BLOG_BASE_URL}/posts/{slug}"


def derive_deck(filepath: Path, deck_prefix: str) -> str:
    """Deck name from category + topic: 'Blog::Linux::Systemd'."""
    parts = filepath.parts
    try:
        posts_idx = parts.index("posts")
        category = parts[posts_idx + 1] if posts_idx + 1 < len(parts) - 1 else "General"
    except ValueError:
        category = "General"
    topic = filepath.stem.capitalize()
    return f"{deck_prefix}::{category.capitalize()}::{topic}"


def parse_anki_blocks(content: str) -> list[dict]:
    """
    Parse <!-- anki ... --> blocks from markdown content.

    Returns list of cards, each with a "type" field:
      Basic: {"type": "basic", "front": ..., "back": ..., "tags": [...]}
      Cloze: {"type": "cloze", "text": ..., "tags": [...]}
    """
    cards = []
    pattern = r"<!--\s*anki\b(.*?)-->"
    blocks = re.findall(pattern, content, re.DOTALL)

    for block in blocks:
        # Split block into sections separated by "cloze:" markers.
        # If no "cloze:" marker exists, C: lines are parsed directly from the block.
        sections = re.split(r"\n(?=cloze:)", block)

        # First section contains Q/A pairs (and possibly bare C: lines)
        qa_section = sections[0]

        # Parse Q/A basic cards
        qa_chunks = re.split(r"\n(?=Q:)", qa_section.strip())
        for chunk in qa_chunks:
            chunk = chunk.strip()
            if not chunk:
                continue

            q_match = re.search(r"Q:\s*(.+?)(?:\n|$)", chunk)
            a_match = re.search(r"A:\s*(.+?)(?:\ntags:|$)", chunk, re.DOTALL)
            tags_match = re.search(r"tags:\s*(.+)", chunk)

            if q_match and a_match:
                card = {
                    "type": "basic",
                    "front": q_match.group(1).strip(),
                    "back": a_match.group(1).strip(),
                    "tags": [],
                }
                if tags_match:
                    card["tags"] = [
                        t.strip() for t in tags_match.group(1).split(",")
                    ]
                cards.append(card)

        # Parse bare C: lines in the first section (no cloze: marker needed)
        for line in qa_section.strip().splitlines():
            line = line.strip()
            c_match = re.match(r"C:\s*(.+)", line)
            if c_match:
                cards.append({
                    "type": "cloze",
                    "text": c_match.group(1).strip(),
                    "tags": [],
                })

        # Remaining sections are explicit cloze groups (with "cloze:" header)
        for cloze_section in sections[1:]:
            lines = cloze_section.strip().splitlines()
            if not lines or not lines[0].strip().startswith("cloze:"):
                continue

            # Check for optional tags line right after "cloze:"
            cloze_tags = []
            c_start = 1
            if len(lines) > 1 and lines[1].strip().startswith("tags:"):
                cloze_tags = [
                    t.strip()
                    for t in lines[1].strip().removeprefix("tags:").split(",")
                    if t.strip()
                ]
                c_start = 2

            for line in lines[c_start:]:
                line = line.strip()
                c_match = re.match(r"C:\s*(.+)", line)
                if c_match:
                    cards.append({
                        "type": "cloze",
                        "text": c_match.group(1).strip(),
                        "tags": list(cloze_tags),
                    })

    return cards


def format_back_html(back: str, source_url: str) -> str:
    """Format the back field as HTML with source link."""
    back_html = back.replace("`", "<code>").replace("\n", "<br>")
    back_html += f'<br><br><a href="{source_url}">📖 Blog source</a>'
    return back_html


def format_cloze_html(text: str, source_url: str) -> str:
    """Format cloze text as HTML: convert backtick code to <code> and append source link."""
    cloze_html = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    cloze_html += f'<br><br><a href="{source_url}">📖 Blog source</a>'
    return cloze_html


# ---------------------------------------------------------------------------
# Sync logic (create / update / remove)
# ---------------------------------------------------------------------------

def fetch_existing_notes(source_tag: str) -> dict[str, dict]:
    """Fetch all Anki notes for a source file and index by lookup key.

    Basic notes are indexed by their Front field, Cloze notes by their Text field.

    Returns: {key_text: {"noteId": int, "model": "basic"|"cloze", "fields": {...}, "tags": [str]}, ...}
    """
    query = f'"tag:{source_tag}"'
    note_ids = find_notes(query)
    if not note_ids:
        return {}

    notes_info = get_notes_info(note_ids)
    index = {}
    for note in notes_info:
        fields = note["fields"]
        # Anki may HTML-encode field values (e.g. < becomes &lt;).
        # Unescape so lookups against plain markdown text succeed.
        if "Front" in fields:
            key = html.unescape(fields["Front"]["value"])
            index[key] = {
                "noteId": note["noteId"],
                "model": "basic",
                "back": fields["Back"]["value"],
                "tags": note.get("tags", []),
            }
        elif "Text" in fields:
            key = html.unescape(fields["Text"]["value"])
            index[key] = {
                "noteId": note["noteId"],
                "model": "cloze",
                "text": fields["Text"]["value"],
                "tags": note.get("tags", []),
            }
    return index


def sync_card_to_anki(
    deck: str,
    card: dict,
    tags: list[str],
    source_url: str,
    existing: dict | None,
) -> str:
    """Sync a single card: create if new, update if changed.

    Args:
        card: Parsed card dict with "type" field ("basic" or "cloze").
        existing: The matching entry from fetch_existing_notes, or None if new.

    Returns: "added", "updated", or "unchanged"
    """
    card_type = card["type"]

    if card_type == "cloze":
        text_html = format_cloze_html(card["text"], source_url)
        if existing is None:
            note = {
                "deckName": deck,
                "modelName": "Cloze",
                "fields": {"Text": text_html},
                "options": {"allowDuplicate": False},
                "tags": tags,
            }
            anki_request("addNote", note=note)
            return "added"

        note_id = existing["noteId"]
        existing_text = existing.get("text", "")
        changed = False
        if existing_text != text_html:
            update_note_fields(note_id, {"Text": text_html})
            changed = True
        if sorted(existing["tags"]) != sorted(tags):
            replace_tags_on_note(note_id, existing["tags"], tags)
            changed = True
        return "updated" if changed else "unchanged"

    # Basic card
    back_html = format_back_html(card["back"], source_url)

    if existing is None:
        note = {
            "deckName": deck,
            "modelName": "Basic",
            "fields": {"Front": card["front"], "Back": back_html},
            "options": {"allowDuplicate": False},
            "tags": tags,
        }
        anki_request("addNote", note=note)
        return "added"

    note_id = existing["noteId"]
    existing_back = existing.get("back", "")
    changed = False

    if existing_back != back_html:
        update_note_fields(note_id, {"Back": back_html})
        changed = True

    if sorted(existing["tags"]) != sorted(tags):
        replace_tags_on_note(note_id, existing["tags"], tags)
        changed = True

    return "updated" if changed else "unchanged"


# ---------------------------------------------------------------------------
# File processing
# ---------------------------------------------------------------------------

def process_file(filepath: Path, deck_prefix: str, dry_run: bool) -> dict:
    """Process a single Hugo markdown file.

    Returns: {"added": N, "updated": N, "unchanged": N, "removed": N}
    """
    stats = {"added": 0, "updated": 0, "unchanged": 0, "removed": 0}
    content = filepath.read_text(encoding="utf-8")
    front_matter = parse_front_matter(content)
    title = front_matter.get("title", filepath.stem)

    cards = parse_anki_blocks(content)
    if not cards:
        return stats

    path_tags = derive_tags_from_path(filepath)
    source_tag = derive_source_tag(filepath)
    source_url = derive_source_url(filepath)
    deck = derive_deck(filepath, deck_prefix)

    # Blog-level tags from Hugo front matter (shared across all cards)
    blog_tags = front_matter.get("tags", [])
    if isinstance(blog_tags, str):
        blog_tags = [t.strip() for t in blog_tags.split(",") if t.strip()]

    # Fetch ALL existing notes for this file in one API call,
    # then match by Front text in Python (avoids search query escaping bugs).
    existing_notes = {}
    if not dry_run:
        existing_notes = fetch_existing_notes(source_tag)

    print(f"\n📄 {filepath} ({title})")
    print(f"   Deck: {deck}")
    print(f"   Source: {source_url}")
    print(f"   Path-tags: {path_tags}")
    print(f"   Blog-tags: {blog_tags}")
    if existing_notes:
        print(f"   Existing cards in Anki: {len(existing_notes)}")

    current_keys = set()
    for card in cards:
        all_tags = list(set(path_tags + blog_tags + card["tags"] + [source_tag]))

        if card["type"] == "cloze":
            lookup_key = format_cloze_html(card["text"], source_url)
            label = f"C: {card['text'][:60]}"
        else:
            lookup_key = card["front"]
            label = f"Q: {card['front'][:60]}"

        current_keys.add(lookup_key)

        if dry_run:
            print(f"   ➕ {label}...")
            print(f"      Tags: {all_tags}")
            stats["added"] += 1
        else:
            try:
                existing = existing_notes.get(lookup_key)
                result = sync_card_to_anki(
                    deck, card, all_tags, source_url, existing,
                )
                icon = {"added": "➕", "updated": "🔄", "unchanged": "✅"}[result]
                print(f"   {icon} [{result}] {label}...")
                stats[result] += 1
            except Exception as e:
                print(f"   ⚠️  Error: {e}")

    # Remove cards that were deleted from the markdown
    if not dry_run:
        stale_ids = []
        for key_text, note in existing_notes.items():
            if key_text not in current_keys:
                stale_ids.append(note["noteId"])
                print(f"   🗑️  Removing: {key_text[:60]}...")
        if stale_ids:
            delete_notes(stale_ids)
        stats["removed"] = len(stale_ids)

    return stats


# ---------------------------------------------------------------------------
# Watch mode
# ---------------------------------------------------------------------------

def watch_files(target: Path, deck_prefix: str, poll_interval: float):
    """Poll for file changes and re-sync on modification."""
    print(f"👀 Watching for changes (poll every {poll_interval}s)... Ctrl+C to stop\n")

    # Build initial mtime snapshot
    def get_files() -> list[Path]:
        if target.is_file():
            return [target]
        return sorted(target.rglob("*.md"))

    mtimes: dict[Path, float] = {}
    for f in get_files():
        mtimes[f] = f.stat().st_mtime

    try:
        while True:
            time.sleep(poll_interval)
            current_files = get_files()

            for f in current_files:
                try:
                    mtime = f.stat().st_mtime
                except OSError:
                    continue

                if f not in mtimes or mtime > mtimes[f]:
                    ts = time.strftime("%H:%M:%S")
                    print(f"\n⏰ [{ts}] Change detected: {f}")

                    # Ensure deck exists
                    deck = derive_deck(f, deck_prefix)
                    ensure_deck(deck)

                    stats = process_file(f, deck_prefix, dry_run=False)
                    print(
                        f"   Result: {stats['added']} added, "
                        f"{stats['updated']} updated, "
                        f"{stats['unchanged']} unchanged, "
                        f"{stats['removed']} removed"
                    )
                    clear_unused_tags()
                    print("   🏷️  Cleared unused tags")
                    mtimes[f] = mtime

            # Detect new files
            for f in current_files:
                if f not in mtimes:
                    mtimes[f] = f.stat().st_mtime

    except KeyboardInterrupt:
        print("\n\n👋 Watch stopped.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Sync Hugo blog posts to Anki")
    parser.add_argument("path", type=Path, help="File or directory to process")
    parser.add_argument("--dry-run", action="store_true", help="Preview without sending to Anki")
    parser.add_argument("--deck", default="Blog", help="Top-level Anki deck name (default: Blog)")
    parser.add_argument("--watch", action="store_true", help="Watch for file changes and auto-sync")
    parser.add_argument(
        "--poll-interval", type=float, default=2.0,
        help="Seconds between polls in watch mode (default: 2.0)",
    )
    args = parser.parse_args()

    target = args.path
    if not (target.is_file() and target.suffix == ".md") and not target.is_dir():
        print(f"ERROR: {target} is not a .md file or directory")
        sys.exit(1)

    if args.watch:
        if args.dry_run:
            print("ERROR: --watch and --dry-run cannot be used together")
            sys.exit(1)
        anki_request("version")
        print("✅ Connected to AnkiConnect")
        watch_files(target, args.deck, args.poll_interval)
        return

    if not args.dry_run:
        anki_request("version")
        print("✅ Connected to AnkiConnect")

    files = []
    if target.is_file():
        files = [target]
    else:
        files = sorted(target.rglob("*.md"))

    if args.dry_run:
        print("🔍 DRY RUN — no cards will be sent to Anki\n")

    totals = {"added": 0, "updated": 0, "unchanged": 0, "removed": 0}
    for f in files:
        if not args.dry_run:
            ensure_deck(derive_deck(f, args.deck))
        stats = process_file(f, args.deck, args.dry_run)
        for k in totals:
            totals[k] += stats[k]

    prefix = "📋 Would sync" if args.dry_run else "✅ Synced"
    print(
        f"\n{prefix}: "
        f"{totals['added']} added, "
        f"{totals['updated']} updated, "
        f"{totals['unchanged']} unchanged, "
        f"{totals['removed']} removed"
    )

    if not args.dry_run:
        clear_unused_tags()
        print("🏷️  Cleared unused tags")


if __name__ == "__main__":
    main()
