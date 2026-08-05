"""
The scheduling half, which Meta does not provide.

Instagram publishes when you call it and not a second later, so a queue file
plus something that wakes up periodically IS the scheduler. Entries are kept
in scripts/queue.json so a schedule is reviewable in a diff like everything
else in this repo.

    python3 reel.py schedule out/motivation/day-01/carousel --at "2026-08-05 18:30"
    python3 reel.py queue                # what is lined up
    python3 reel.py queue --run          # publish anything now due

`queue --run` is the bit a cron/launchd job calls. It is safe to run often:
an entry only moves out of `pending` once, and a failure records the reason
instead of retrying forever into a rate limit.
"""

import json
from datetime import datetime
from pathlib import Path

from .config import ROOT
from .publish import PublishError, publish_dir

QUEUE = ROOT / "scripts" / "queue.json"

# What a human is likely to type, shortest first. ISO-8601 with a timezone
# also parses, via fromisoformat below.
FORMATS = ("%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S")


def parse_when(text):
    """
    Turn a typed time into an aware datetime in the machine's own zone.

    Naive input means local time -- posting is a local-clock decision ("18:30,
    when people are on their phones"), not a UTC one.
    """
    for fmt in FORMATS:
        try:
            return datetime.strptime(text, fmt).astimezone()
        except ValueError:
            pass
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        raise SystemExit(
            f"could not read {text!r} as a time. Try '2026-08-05 18:30'."
        ) from None
    return parsed if parsed.tzinfo else parsed.astimezone()


def load():
    if not QUEUE.exists():
        return []
    return json.loads(QUEUE.read_text(encoding="utf-8"))


def save(entries):
    entries = sorted(entries, key=lambda e: e["at"])
    QUEUE.parent.mkdir(parents=True, exist_ok=True)
    # Written via a temp file so a crash mid-write cannot leave the queue
    # unreadable and silently stop every future post.
    tmp = QUEUE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")
    tmp.replace(QUEUE)
    return entries


def add(directory, when, share_to_feed=True):
    directory = str(Path(directory))
    entries = load()
    for entry in entries:
        if entry["dir"] == directory and entry["status"] == "pending":
            raise SystemExit(f"{directory} is already queued for {entry['at']}")
    entries.append({
        "dir": directory,
        "at": parse_when(when).isoformat(),
        "share_to_feed": share_to_feed,
        "status": "pending",
    })
    return save(entries)


def due(entries, now=None):
    now = now or datetime.now().astimezone()
    return [e for e in entries
            if e["status"] == "pending" and parse_when(e["at"]) <= now]


def run(now=None, dry_run=False):
    """Publish everything now due. Returns (published, failed)."""
    entries = load()
    ready = due(entries, now)
    if not ready:
        return 0, 0

    published = failed = 0
    for entry in ready:
        path = ROOT / entry["dir"]
        print(f"-- {entry['at']}  {entry['dir']}")
        try:
            media_id = publish_dir(
                path, dry_run=dry_run,
                share_to_feed=entry.get("share_to_feed", True),
            )
        except (PublishError, SystemExit, OSError) as e:
            entry["status"] = "failed"
            entry["error"] = str(e)[:500]
            failed += 1
            print(f"   ! {e}")
        else:
            if dry_run:
                continue
            entry["status"] = "published"
            entry["media_id"] = media_id
            entry["published_at"] = datetime.now().astimezone().isoformat()
            published += 1
            print(f"   published {media_id}")
        # Saved per entry, not at the end: if the run dies halfway, the posts
        # that did go out must not look pending on the next tick.
        save(entries)

    return published, failed


def show(entries):
    if not entries:
        print("queue is empty")
        return
    for entry in entries:
        mark = {"pending": " ", "published": "x", "failed": "!"}.get(entry["status"], "?")
        line = f"  [{mark}] {entry['at']}  {entry['dir']}"
        if entry.get("error"):
            line += f"\n        {entry['error'][:120]}"
        print(line)
