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


class HashtagCountTests(unittest.TestCase):
    def test_tags_are_counted_wherever_they_sit_in_the_caption(self):
        """The count only drives the over-limit warning, and tags are written
        inline now, so a counter that only looked at a trailing block would
        under-report and the warning would never fire."""
        self.assertEqual(
            post.count_hashtags("Why #Pluto lost it.\n\n#space #astronomy"), 3)

    def test_a_lone_hash_is_not_a_tag(self):
        """'#' on its own is punctuation. Counting it would push a caption over
        the limit and print a warning about a tag that does not exist."""
        self.assertEqual(post.count_hashtags("number # 9 and #space"), 1)


class RenderTests(unittest.TestCase):
    def test_the_caption_is_passed_through_verbatim(self):
        """The caption is written the way it will be pasted. Anything that
        reflows or re-orders it means the script stops showing the real post."""
        body = "Pluto never moved.\n\nOne a day.\n\n#pluto #space"
        self.assertEqual(post.render(FakeScript(post={"caption": body})), body)

    def test_surrounding_whitespace_is_trimmed(self):
        """A caption pasted with a leading blank line shows as an empty first
        line in the app, which reads as a mistake."""
        self.assertEqual(
            post.render(FakeScript(post={"caption": "\n  #space  \n"})),
            "#space")

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
