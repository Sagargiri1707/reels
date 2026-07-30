"""
Tests for timeline.py -- the only module where a bug is invisible until the
finished video is watched.

Each test states the failure it is guarding against, because "it returns three
spans" is not worth asserting on its own.
"""

import sys
import unittest
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from reelkit import timeline  # noqa: E402


@dataclass
class FakeBeat:
    id: str
    text: str
    index: int = 0


def seg(text, start, end):
    return {"text": text, "start": start, "end": end}


BEATS = [
    FakeBeat("01", "Venus spins backwards."),
    FakeBeat("02", "Mars is rust."),
]

# One segment per word, the shape fish returns for short narration.
PERFECT = {
    "audio_duration": 6.0,
    "segments": [
        seg("Venus", 0.0, 0.5), seg("spins", 0.5, 1.0), seg("backwards.", 1.0, 1.8),
        seg("Mars", 2.4, 2.9), seg("is", 2.9, 3.1), seg("rust.", 3.1, 3.8),
    ],
}


class TestCutPoints(unittest.TestCase):

    def test_image_holds_until_the_next_beat_speaks(self):
        """A beat must not cut on its own last word -- that would flash the
        paper background during the pause before the next line."""
        spans = timeline.build(BEATS, PERFECT)
        self.assertEqual(spans[0].end, 2.4)          # not 1.8, the last word
        self.assertEqual(spans[1].start, 2.4)
        self.assertAlmostEqual(spans[0].end, spans[1].start)

    def test_first_beat_starts_at_zero(self):
        """Leading silence belongs to beat one; starting at its first word
        would leave the reel's opening frames empty."""
        self.assertEqual(timeline.build(BEATS, PERFECT)[0].start, 0.0)

    def test_last_beat_runs_to_the_end_of_the_audio(self):
        """Trailing silence must be covered or the video ends before the
        narration does and ffmpeg pads it with nothing."""
        spans = timeline.build(BEATS, PERFECT)
        self.assertEqual(spans[-1].end, 6.0)

    def test_spans_are_gapless_and_ordered(self):
        spans = timeline.build(BEATS, PERFECT)
        for a, b in zip(spans, spans[1:]):
            self.assertEqual(a.end, b.start)
            self.assertGreater(a.duration, 0)


class TestMismatch(unittest.TestCase):

    def test_word_count_mismatch_refuses_to_guess(self):
        """The whole reason this module exists. If the voice spoke a different
        number of words, every cut after the divergence is wrong. Guessing
        produces a video that looks fine to the renderer and broken to a
        viewer, so it must fail instead."""
        short = {
            "audio_duration": 6.0,
            "segments": [seg("Venus", 0.0, 0.5), seg("spins", 0.5, 1.0)],
        }
        with self.assertRaises(timeline.AlignmentMismatch) as ctx:
            timeline.build(BEATS, short)
        self.assertIn("6 words", str(ctx.exception))
        self.assertIn("2", str(ctx.exception))

    def test_extra_spoken_words_are_an_error(self):
        """Words the script does not account for mean the narration text and
        the beats have drifted apart -- usually an edit to one and not the
        other."""
        long = dict(PERFECT)
        long["segments"] = PERFECT["segments"] + [seg("Extra", 4.0, 4.5)]
        with self.assertRaises(timeline.AlignmentMismatch):
            timeline.build(BEATS, long)

    def test_contraction_expansion_falls_back_to_position(self):
        """TTS is allowed to say "we have" for "we've". The word count still
        matches, so the cuts are recoverable and the build should continue
        rather than block on a cosmetic difference."""
        beats = [FakeBeat("01", "We've found life."), FakeBeat("02", "Mars is rust.")]
        alignment = {
            "audio_duration": 6.0,
            "segments": [
                seg("We", 0.0, 0.4), seg("found", 0.4, 0.9), seg("life.", 0.9, 1.5),
                seg("Mars", 2.4, 2.9), seg("is", 2.9, 3.1), seg("rust.", 3.1, 3.8),
            ],
        }
        spans = timeline.build(beats, alignment)
        self.assertEqual(spans[0].end, 2.4)

    def test_punctuation_and_case_never_count_as_a_mismatch(self):
        """The script writes "backwards." and the aligner may return
        "Backwards" -- identical words as far as timing is concerned."""
        alignment = {
            "audio_duration": 6.0,
            "segments": [
                seg("venus", 0.0, 0.5), seg("SPINS", 0.5, 1.0), seg("backwards", 1.0, 1.8),
                seg("mars!", 2.4, 2.9), seg("Is", 2.9, 3.1), seg("RUST", 3.1, 3.8),
            ],
        }
        spans = timeline.build(BEATS, alignment)   # must not raise
        self.assertEqual(len(spans), 2)


class TestSegmentSplitting(unittest.TestCase):

    def test_phrase_segments_are_split_into_words(self):
        """fish may return a phrase per segment instead of a word. Captions
        need per-word timings, so a phrase must be divided rather than dropped
        or treated as a single word."""
        words = timeline.flatten_segments([seg("Venus spins", 0.0, 1.0)])
        self.assertEqual([w.text for w in words], ["Venus", "spins"])
        self.assertEqual(words[0].start, 0.0)
        self.assertEqual(words[-1].end, 1.0)
        self.assertEqual(words[0].end, words[1].start)

    def test_longer_words_get_proportionally_more_time(self):
        """Splitting a phrase evenly would drift the caption off a long word.
        Length is a cheap proxy for how long it takes to say."""
        words = timeline.flatten_segments([seg("a considerable", 0.0, 1.0)])
        self.assertLess(words[0].end - words[0].start,
                        words[1].end - words[1].start)


class TestCaptions(unittest.TestCase):

    def test_cards_are_continuous_so_text_never_disappears(self):
        """A gap between cards shows a bare frame mid-sentence, which reads as
        a rendering glitch."""
        span = timeline.build(BEATS, PERFECT)[0]
        cards = timeline.caption_chunks(span, 2)
        for a, b in zip(cards, cards[1:]):
            self.assertEqual(a[1], b[0])
        self.assertEqual(cards[-1][1], span.end)

    def test_cards_group_by_the_requested_size(self):
        span = timeline.build(BEATS, PERFECT)[0]
        self.assertEqual([c[2] for c in timeline.caption_chunks(span, 2)],
                         ["Venus spins", "backwards."])

    def test_first_card_starts_when_the_word_is_spoken(self):
        """Beat one starts at 0.0 to cover the lead-in silence, but its caption
        must wait for the voice or the text appears before it is said."""
        span = timeline.build(BEATS, PERFECT)[0]
        self.assertEqual(timeline.caption_chunks(span, 3)[0][0], 0.0)


class TestEvenSplit(unittest.TestCase):

    def test_share_is_proportional_to_word_count(self):
        """The escape hatch still has to be better than equal slices -- a
        twelve word beat needs more screen time than a four word beat."""
        beats = [FakeBeat("01", "one two three"), FakeBeat("02", "four")]
        spans = timeline.even_split(beats, 8.0)
        self.assertAlmostEqual(spans[0].duration, 6.0)
        self.assertAlmostEqual(spans[1].duration, 2.0)

    def test_covers_the_whole_runtime(self):
        beats = [FakeBeat("01", "a b"), FakeBeat("02", "c d e")]
        spans = timeline.even_split(beats, 10.0)
        self.assertEqual(spans[0].start, 0.0)
        self.assertEqual(spans[-1].end, 10.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
