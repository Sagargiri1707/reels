"""
Tests for the publish queue.

Meta gives no scheduling endpoint, so this queue is the only record of what
has already gone out. The failures that matter are all about that bookkeeping:
posting something twice is worse than posting it late, a post that goes out
while a later one fails must not be replayed on the next tick, and an entry
must never fire early because a timezone was dropped somewhere.
"""

import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from reelkit import schedule  # noqa: E402


class QueueTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self._real_queue, self._real_root = schedule.QUEUE, schedule.ROOT
        schedule.QUEUE = root / "scripts" / "queue.json"
        schedule.ROOT = root
        self.addCleanup(self._restore)
        self.published = []

    def _restore(self):
        schedule.QUEUE, schedule.ROOT = self._real_queue, self._real_root

    def _stub_publish(self, fail_on=()):
        """Stand in for the network call, recording what it was asked to post."""
        def fake(directory, dry_run=False, share_to_feed=True):
            name = Path(directory).name
            if name in fail_on:
                raise schedule.PublishError("meta said no")
            if not dry_run:
                self.published.append(name)
            return None if dry_run else f"media-{name}"
        original = schedule.publish_dir
        self.addCleanup(setattr, schedule, "publish_dir", original)
        schedule.publish_dir = fake

    # -- ordering ---------------------------------------------------------

    def test_only_entries_past_their_time_are_due(self):
        """An entry firing early posts to an empty audience -- worse than late."""
        now = datetime(2026, 8, 4, 18, 0).astimezone()
        schedule.add("out/a", "2026-08-04 17:59")
        schedule.add("out/b", "2026-08-04 18:01")

        due = schedule.due(schedule.load(), now=now)

        self.assertEqual([e["dir"] for e in due], ["out/a"])

    def test_naive_times_are_read_as_local_not_utc(self):
        """
        "18:30" means 18:30 where the person posting lives. Reading it as UTC
        silently shifts every post in the queue by the offset.
        """
        parsed = schedule.parse_when("2026-08-04 18:30")

        self.assertIsNotNone(parsed.tzinfo)
        self.assertEqual(parsed.utcoffset(),
                         datetime(2026, 8, 4, 18, 30).astimezone().utcoffset())

    def test_explicit_offset_survives_a_round_trip_through_the_file(self):
        """A queued time must mean the same thing after it is written to disk."""
        schedule.add("out/a", "2026-08-04T18:30:00+00:00")

        stored = schedule.parse_when(schedule.load()[0]["at"])

        self.assertEqual(stored,
                         datetime(2026, 8, 4, 18, 30, tzinfo=timezone.utc))

    # -- not posting twice ------------------------------------------------

    def test_a_published_entry_is_never_picked_up_again(self):
        """The whole point of the status field: a second tick must be a no-op."""
        self._stub_publish()
        past = (datetime.now().astimezone() - timedelta(hours=1)).isoformat()
        schedule.add("out/a", past)

        schedule.run()
        schedule.run()

        self.assertEqual(self.published, ["a"])
        self.assertEqual(schedule.load()[0]["status"], "published")

    def test_a_failure_does_not_replay_the_posts_that_worked(self):
        """
        Meta's cap is 100 posts a rolling 24h. A run that re-posts everything
        after one bad entry burns that cap and duplicates the feed.
        """
        self._stub_publish(fail_on=("b",))
        past = datetime.now().astimezone() - timedelta(hours=1)
        for name, offset in (("a", 3), ("b", 2), ("c", 1)):
            schedule.add(f"out/{name}", (past - timedelta(minutes=offset)).isoformat())

        published, failed = schedule.run()
        schedule.run()

        self.assertEqual((published, failed), (2, 1))
        self.assertEqual(self.published, ["a", "c"])

    def test_a_failure_keeps_metas_reason_for_the_next_person(self):
        """A silent `failed` gives nothing to act on when a slot is missed."""
        self._stub_publish(fail_on=("a",))
        past = (datetime.now().astimezone() - timedelta(hours=1)).isoformat()
        schedule.add("out/a", past)

        schedule.run()

        entry = schedule.load()[0]
        self.assertEqual(entry["status"], "failed")
        self.assertIn("meta said no", entry["error"])

    def test_queueing_the_same_directory_twice_is_refused(self):
        """Double-queueing is how the same reel goes out twice."""
        schedule.add("out/a", "2026-08-04 18:00")

        with self.assertRaises(SystemExit):
            schedule.add("out/a", "2026-08-05 18:00")

    def test_a_dry_run_leaves_every_entry_pending(self):
        """Dry runs are for checking the schedule, not consuming it."""
        self._stub_publish()
        past = (datetime.now().astimezone() - timedelta(hours=1)).isoformat()
        schedule.add("out/a", past)

        schedule.run(dry_run=True)

        self.assertEqual(schedule.load()[0]["status"], "pending")

    # -- the file itself --------------------------------------------------

    def test_the_queue_file_stays_readable_json_sorted_by_time(self):
        """Cron reads this unattended -- an unparseable queue posts nothing."""
        schedule.add("out/b", "2026-08-06 18:00")
        schedule.add("out/a", "2026-08-05 18:00")

        raw = json.loads(schedule.QUEUE.read_text(encoding="utf-8"))

        self.assertEqual([e["dir"] for e in raw], ["out/a", "out/b"])


if __name__ == "__main__":
    unittest.main()
