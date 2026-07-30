"""
Tests for post.py and the frame-picking logic in thumbs.py.

Both feed things a human copies straight into an app, so a bug here is not
caught by watching the video -- it shows up as a broken caption or the wrong
cover after the reel is already live. Each test names the failure it guards.
"""

import sys
import unittest
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from reelkit import post, thumbs  # noqa: E402


@dataclass
class FakeScript:
    post: dict = field(default_factory=dict)


@dataclass
class FakeSpan:
    id: str
    index: int
    start: float
    end: float

    @property
    def duration(self):
        return self.end - self.start


class HashtagTests(unittest.TestCase):
    def test_bare_words_become_tags(self):
        """A script is hand-edited, so tags get written without the hash as
        often as with it. Both must post identically."""
        self.assertEqual(
            post.hashtags({"hashtags": ["space", "#physics"]}),
            ["#space", "#physics"],
        )

    def test_a_single_string_is_accepted(self):
        """'space physics' is the natural thing to type into one JSON field.
        Silently treating it as one giant tag would post '#space physics'."""
        self.assertEqual(
            post.hashtags({"hashtags": "space #physics"}),
            ["#space", "#physics"],
        )

    def test_duplicates_are_dropped_case_insensitively(self):
        """Apps cap the tag count. A repeat spends a slot and reaches nobody
        new, and #Space vs #space is the same tag to the platform."""
        self.assertEqual(
            post.hashtags({"hashtags": ["space", "Space", "#SPACE", "moon"]}),
            ["#space", "#moon"],
        )

    def test_empty_entries_never_produce_a_lone_hash(self):
        """A stray '' or '#' would render as a bare '#', which reads as a typo
        in the caption."""
        self.assertEqual(post.hashtags({"hashtags": ["", "#", "  ", "space"]}),
                         ["#space"])


class RenderTests(unittest.TestCase):
    def test_caption_and_tags_are_separated_by_a_blank_line(self):
        """The tags must be visually detachable from the sentence; run
        together, the caption reads as spam."""
        s = FakeScript(post={"caption": "Gravity is not a force.",
                             "hashtags": ["space"]})
        self.assertEqual(post.render(s), "Gravity is not a force.\n\n#space\n")

    def test_missing_caption_still_renders_the_tags(self):
        """Half-finished scripts are normal mid-session; losing the tags that
        were already written would be silent data loss."""
        s = FakeScript(post={"caption": "", "hashtags": ["space"]})
        self.assertEqual(post.render(s), "#space\n")

    def test_nothing_authored_renders_nothing(self):
        """An empty string is the signal write() uses to warn instead of
        writing a file that looks finished but is blank."""
        self.assertEqual(post.render(FakeScript(post={})), "")


class FrameTimeTests(unittest.TestCase):
    def test_frame_is_taken_from_the_middle_of_the_beat(self):
        """At a beat's start the Ken Burns move has not begun and the caption
        card may not have appeared, so a start-frame cover under-sells the
        beat it came from."""
        self.assertAlmostEqual(
            thumbs.frame_time(FakeSpan("01", 0, 2.0, 6.0)), 4.0)


class SelectTests(unittest.TestCase):
    def setUp(self):
        self.made = [(FakeSpan("01", 0, 0.0, 2.0), Path("/tmp/01.jpg")),
                     (FakeSpan("07", 1, 2.0, 4.0), Path("/tmp/07.jpg"))]

    def test_unknown_beat_id_is_refused_rather_than_guessed(self):
        """Falling back to the hook on a typo would hand back a cover the user
        did not choose and never told them."""
        s = FakeScript(post={"thumbnail_beat": "99"})
        with self.assertRaises(SystemExit) as cm:
            thumbs.choose(s, self.made)
        self.assertIn("01, 07", str(cm.exception))

    def test_flag_overrides_the_script(self):
        """`--beat` exists to try an alternative cover without editing the
        script; if the script won, the flag would look broken."""
        s = FakeScript(post={"thumbnail_beat": "01"})
        self.assertEqual(thumbs.choose(s, self.made, beat="07"),
                         Path("/tmp/07.jpg"))

    def test_hook_is_the_default_cover(self):
        """The script was written so beat 1 stops the scroll; with nothing
        specified that is the right frame to lead with."""
        self.assertEqual(thumbs.choose(FakeScript(post={}), self.made),
                         Path("/tmp/01.jpg"))

    def test_a_numeric_beat_id_still_matches(self):
        """Beat ids are strings in the script but JSON invites writing 1
        instead of "01"; a silent no-match here would abort a finished render."""
        made = [(FakeSpan("1", 0, 0.0, 2.0), Path("/tmp/1.jpg"))]
        s = FakeScript(post={"thumbnail_beat": 1})
        self.assertEqual(thumbs.choose(s, made), Path("/tmp/1.jpg"))


if __name__ == "__main__":
    unittest.main()
