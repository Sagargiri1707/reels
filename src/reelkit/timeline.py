"""
Turn one continuous narration plus its alignment into per-beat cut points.

This is the only real logic in the pipeline and it touches no network and no
filesystem, so it is unit tested directly.

The contract: the narration text is exactly the beats' text joined in order,
so the alignment's words must line up with the beats' words one for one. When
they do not -- because TTS normalised "8" to "eight", or dropped a token -- we
say so with the exact position rather than guessing, because a guess here
desyncs every frame after it.
"""

import re
from dataclasses import dataclass

WORD_CHARS = re.compile(r"[^a-z0-9]+")


@dataclass
class Word:
    text: str
    start: float
    end: float


@dataclass
class Span:
    """One beat's slice of the timeline."""
    id: str
    index: int
    start: float
    end: float
    words: list

    @property
    def duration(self):
        return self.end - self.start


class AlignmentMismatch(RuntimeError):
    pass


def normalize(word):
    """Compare on letters and digits only. Punctuation and case are things
    TTS is entitled to reinterpret; the word itself is not."""
    return WORD_CHARS.sub("", word.lower())


def flatten_segments(segments):
    """
    Alignment segments may each cover a word or a whole phrase. Split them
    into words, sharing a segment's span between its words in proportion to
    their length, so multi-word segments still give usable caption timings.
    """
    words = []
    for seg in segments:
        parts = [p for p in str(seg.get("text", "")).split() if p]
        if not parts:
            continue
        start = float(seg["start"])
        end = float(seg["end"])
        if len(parts) == 1:
            words.append(Word(parts[0], start, end))
            continue

        total = sum(len(p) for p in parts) or len(parts)
        span = max(end - start, 0.0)
        cursor = start
        for i, part in enumerate(parts):
            share = span * (len(part) / total)
            w_end = end if i == len(parts) - 1 else cursor + share
            words.append(Word(part, cursor, w_end))
            cursor = w_end
    return words


def _beat_word_counts(beats):
    return [[w for w in b.text.split() if normalize(w)] for b in beats]


def _strict_walk(beats, beat_words, flat):
    """Consume flat words beat by beat, requiring each to match."""
    spans, cursor = [], 0
    for beat, words in zip(beats, beat_words):
        take = flat[cursor:cursor + len(words)]
        if len(take) < len(words):
            raise AlignmentMismatch(
                f"beat {beat.id!r} ran past the end of the alignment: needed "
                f"{len(words)} words, only {len(take)} left"
            )
        for i, (expected, got) in enumerate(zip(words, take)):
            if normalize(expected) != normalize(got.text):
                raise AlignmentMismatch(
                    f"beat {beat.id!r} word {i + 1}: script says "
                    f"{expected!r} but the voice said {got.text!r}\n"
                    f"  script : {' '.join(words[max(0, i - 2):i + 3])}\n"
                    f"  voice  : {' '.join(w.text for w in take[max(0, i - 2):i + 3])}"
                )
        spans.append(take)
        cursor += len(words)

    leftover = len(flat) - cursor
    if leftover > 0:
        raise AlignmentMismatch(
            f"{leftover} spoken words are not covered by any beat, starting at "
            f"{flat[cursor].text!r} ({flat[cursor].start:.2f}s)"
        )
    return spans


def _positional_split(beats, beat_words, flat):
    """
    Counts line up but some words differ -- normal when TTS expands a
    contraction. Slice by position and report what differed rather than
    failing the whole build.
    """
    spans, cursor, notes = [], 0, []
    for beat, words in zip(beats, beat_words):
        take = flat[cursor:cursor + len(words)]
        for expected, got in zip(words, take):
            if normalize(expected) != normalize(got.text):
                notes.append(f"beat {beat.id}: {expected!r} -> {got.text!r}")
        spans.append(take)
        cursor += len(words)
    return spans, notes


def build(beats, alignment, strict=True):
    """
    beats     : objects with .id, .index and .text
    alignment : {"segments": [{"text","start","end"}], "audio_duration": float}

    Returns [Span]. A beat holds the frame until the next beat's first word,
    so there is never a gap between images.
    """
    segments = alignment.get("segments") or []
    audio_duration = float(alignment.get("audio_duration") or 0.0)
    flat = flatten_segments(segments)
    if not flat:
        raise AlignmentMismatch("alignment contains no words")

    beat_words = _beat_word_counts(beats)
    expected_total = sum(len(w) for w in beat_words)

    try:
        taken = _strict_walk(beats, beat_words, flat)
    except AlignmentMismatch:
        if strict and expected_total != len(flat):
            raise AlignmentMismatch(
                f"the script has {expected_total} words but the voice spoke "
                f"{len(flat)}. The beats cannot be cut safely.\n"
                "Fix the script text, re-run `voice --force`, or accept even "
                "spacing with `--even-split`."
            ) from None
        taken, notes = _positional_split(beats, beat_words, flat)
        if notes:
            print("  ! alignment differed on some words, split by position:")
            for n in notes[:8]:
                print(f"      {n}")
            if len(notes) > 8:
                print(f"      ... and {len(notes) - 8} more")

    if not audio_duration:
        audio_duration = flat[-1].end

    spans = []
    for i, (beat, words) in enumerate(zip(beats, taken)):
        start = words[0].start if i > 0 else 0.0
        # Hold each image until the next beat actually starts speaking.
        if i + 1 < len(taken) and taken[i + 1]:
            end = taken[i + 1][0].start
        else:
            end = audio_duration
        if end <= start:
            raise AlignmentMismatch(
                f"beat {beat.id!r} has non-positive duration "
                f"({start:.2f}s -> {end:.2f}s)"
            )
        spans.append(Span(id=beat.id, index=i, start=start, end=end, words=words))
    return spans


def even_split(beats, audio_duration):
    """
    Escape hatch for when alignment is unusable: give each beat a share of the
    runtime proportional to its word count. Never as tight as real timings.
    """
    counts = [max(1, len(b.text.split())) for b in beats]
    total = sum(counts)
    spans, cursor = [], 0.0
    for i, (beat, n) in enumerate(zip(beats, counts)):
        end = audio_duration if i == len(beats) - 1 else \
            cursor + audio_duration * (n / total)
        words = [Word(w, cursor, end) for w in beat.text.split()]
        spans.append(Span(id=beat.id, index=i, start=cursor, end=end, words=words))
        cursor = end
    return spans


def caption_chunks(span, words_per_chunk):
    """
    Group a beat's words into caption cards. Each card runs until the next one
    begins so a caption is always on screen, and the last card of a beat holds
    to the beat's end.
    """
    if not span.words:
        return []
    n = max(1, int(words_per_chunk))
    groups = [span.words[i:i + n] for i in range(0, len(span.words), n)]
    cards = []
    for i, group in enumerate(groups):
        start = group[0].start
        end = groups[i + 1][0].start if i + 1 < len(groups) else span.end
        cards.append((start, max(end, start + 0.05), " ".join(w.text for w in group)))
    return cards
