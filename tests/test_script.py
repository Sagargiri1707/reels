"""
Tests for prompt assembly and the full-prompt contract in script.py.

What the model is sent is the one thing in this pipeline nobody can eyeball
after the fact -- a prompt that quietly lost its style lock or its text rule
comes back as a plausible image that does not match the other eleven, and the
first sign of it is a finished reel that looks wrong. Each test names the
frame it is protecting.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from reelkit import script as script_mod  # noqa: E402

LOCK = "fine black ink and pencil drawing, large negative space"
ANCHOR = "the solar system: planets, orbits, telescopes, the night sky"
CANVAS = "1152x2048"
PAPER_0 = "#F2EDE4"   # first tone in the default palette


def full_prompt(scene, paper=PAPER_0, text_rule=script_mod.NO_TEXT_MARKER):
    """A prompt in the shape the authoring pass is contracted to write: canvas,
    scene, anchor, lock verbatim, paper, text rule -- nothing appended later."""
    return (f"{CANVAS} vertical portrait canvas. {scene}. {ANCHOR}. {LOCK}. "
            f"drawn on warm off-white paper, flat background colour {paper}. "
            f"{text_rule} anywhere in the image.")


def write_script(tmp, **overrides):
    data = {
        "topic": "test",
        "slug": "test-01",
        "subject_anchor": ANCHOR,
        "style_lock": LOCK,
        "voice": {"reference_id": "abc123"},
        "outro": False,
        "beats": [{"id": "01", "text": "A line.", "image_prompt": "a marble"}],
    }
    data.update(overrides)
    path = Path(tmp) / "test-01.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


class AssembledPromptTests(unittest.TestCase):
    """The original mode has to keep behaving exactly as it did -- every script
    already in scripts/ is on it, and a changed prompt means a changed hash
    means re-paying for images that are already on disk."""

    def load(self, **overrides):
        with tempfile.TemporaryDirectory() as tmp:
            return script_mod.load(write_script(tmp, **overrides))

    def test_assembled_is_still_the_default(self):
        """Nothing in a committed script says prompt_format, so the default is
        what every existing reel renders on."""
        s = self.load()
        self.assertEqual(s.prompt_format, "assembled")

    def test_scene_gets_anchor_lock_paper_and_text_rule_welded_on(self):
        """The beat carries a scene only; if any one of these four stopped
        being appended the frame would drift off topic, off style, off paper
        or come back captioned in gibberish."""
        s = self.load()
        prompt = s.prompt_for(s.beats[0])
        self.assertTrue(prompt.startswith("a marble"))
        self.assertIn(ANCHOR, prompt)
        self.assertIn(LOCK, prompt)
        self.assertIn(PAPER_0, prompt)
        self.assertTrue(prompt.endswith(script_mod.NO_TEXT_RULE))

    def test_a_lettered_beat_swaps_the_no_text_rule_for_its_words(self):
        """Both rules appearing at once is a contradiction the model resolves
        by inventing something."""
        s = self.load(beats=[{"id": "01", "text": "A line.",
                              "image_prompt": "a plaque", "image_text": "PLUTO"}])
        prompt = s.prompt_for(s.beats[0])
        self.assertIn("'PLUTO'", prompt)
        self.assertNotIn(script_mod.NO_TEXT_MARKER, prompt)


class FullPromptTests(unittest.TestCase):
    """Full mode is the dolze-server shape: one authoring pass writes the whole
    prompt and the pipeline sends it untouched."""

    def load(self, **overrides):
        with tempfile.TemporaryDirectory() as tmp:
            return script_mod.load(write_script(tmp, prompt_format="full",
                                                **overrides))

    def test_a_full_prompt_reaches_the_model_byte_for_byte(self):
        """The whole point of the mode: what is in the file is what was sent,
        so a bad frame is debugged by reading the script rather than by
        re-deriving what the code appended to it."""
        written = full_prompt("a marble held up to a window")
        s = self.load(beats=[{"id": "01", "text": "A line.",
                              "image_prompt": written}])
        self.assertEqual(s.prompt_for(s.beats[0]), written)

    def test_the_outro_stays_assembled_inside_a_full_script(self):
        """The sign-off is pipeline-owned and its paper tone falls out of the
        beat count, so it cannot be baked. If the script mode leaked onto it,
        loading any full script with an outro would fail the contract check."""
        s = self.load(outro=True,
                      beats=[{"id": "01", "text": "A line.",
                              "image_prompt": full_prompt("a marble")}])
        outro = s.beats[-1]
        self.assertEqual(outro.id, "outro")
        self.assertEqual(outro.prompt_format, "assembled")
        self.assertIn(LOCK, s.prompt_for(outro))

    def _rejects(self, prompt, fragment, **overrides):
        beat = {"id": "01", "text": "A line.", "image_prompt": prompt}
        beat.update(overrides)
        with self.assertRaises(SystemExit) as caught:
            self.load(beats=[beat])
        self.assertIn(fragment, str(caught.exception))

    def test_a_prompt_missing_the_style_lock_is_refused(self):
        """Nothing appends the lock any more, so a prompt written without it
        renders a frame in its own style and the reel stops matching itself."""
        self._rejects(full_prompt("a marble").replace(LOCK, "nice drawing"),
                      "style_lock verbatim")

    def test_a_reworded_style_lock_is_refused(self):
        """Near enough is the drift this check exists to catch: the lock is
        one string reused unchanged, not a description to paraphrase."""
        self._rejects(full_prompt("a marble").replace(LOCK, LOCK.upper()),
                      "style_lock verbatim")

    def test_a_prompt_that_never_states_the_canvas_is_refused(self):
        """The model follows the prompt text over the size parameter; without
        the canvas in words it composes for a landscape frame and the subject
        ends up cropped out of a 9:16 render."""
        self._rejects(full_prompt("a marble").replace(CANVAS, ""),
                      "canvas '1152x2048'")

    def test_a_prompt_carrying_the_wrong_paper_tone_is_refused(self):
        """Paper rotates by beat position so neighbouring frames never share a
        background. A prompt naming some other tone silently breaks the one
        thing that makes a cut land."""
        self._rejects(full_prompt("a marble", paper="#DFE4E9"),
                      "paper colour #F2EDE4")

    def test_a_prompt_with_no_text_rule_at_all_is_refused(self):
        """An unconstrained frame comes back lettered with invented captions,
        which is the most obviously-AI thing a frame can do."""
        self._rejects(full_prompt("a marble", text_rule="quiet composition"),
                      "no text rule")

    def test_a_lettered_beat_whose_prompt_omits_the_word_is_refused(self):
        """image_text is what the build believes is on screen -- the cover
        picker and the caption both read it. A prompt that never asks for the
        word leaves that belief false."""
        self._rejects(full_prompt("a plaque",
                                  text_rule="the only writing is a short name"),
                      "does not contain the image_text 'PLUTO'",
                      image_text="PLUTO")

    def test_a_lettered_beat_passes_when_its_prompt_asks_for_the_word(self):
        s = self.load(beats=[{
            "id": "01", "text": "A line.", "image_text": "PLUTO",
            "image_prompt": full_prompt("a plaque",
                                        text_rule="the only writing is PLUTO"),
        }])
        self.assertIn("PLUTO", s.prompt_for(s.beats[0]))


class PromptFormatValidationTests(unittest.TestCase):
    def test_an_unknown_format_is_refused_by_name(self):
        """A typo like 'complete' would otherwise fall through as assembled and
        double-append style onto prompts that already carry it."""
        with tempfile.TemporaryDirectory() as tmp:
            path = write_script(tmp, prompt_format="complete")
            with self.assertRaises(SystemExit) as caught:
                script_mod.load(path)
        self.assertIn("prompt_format 'complete'", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
