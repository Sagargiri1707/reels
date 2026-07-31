"""
Tests for the concurrent render loop in images.py.

Every file this module writes cost money, so the failure that matters is not a
crash -- it is a run that half-succeeds and then loses track of which half. A
beat that rendered must survive a sibling that did not, and a beat that failed
must never be reported as done.
"""

import json
import sys
import tempfile
import unittest
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from reelkit import images  # noqa: E402


@dataclass
class FakeBeat:
    id: str
    image_prompt: str = "a marble"


@dataclass
class FakeScript:
    root: Path
    beats: list
    image: dict = field(default_factory=lambda: {
        "model": "openai/gpt-image-2",
        "image_size": {"width": 1152, "height": 2048},
        "quality": "low",
        "concurrency": 4,
    })

    @property
    def path(self):
        return self.root / "test-01.json"

    @property
    def assets_dir(self):
        return self.root / "assets"

    @property
    def manifest_path(self):
        return self.assets_dir / "manifest.json"

    def image_path(self, beat):
        return self.assets_dir / f"{beat.id}.png"

    def prompt_for(self, beat):
        return beat.image_prompt


class GenerateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.script = FakeScript(root=self.root,
                                 beats=[FakeBeat("01"), FakeBeat("02"),
                                        FakeBeat("03")])
        self.rendered = []
        real_render = images._render
        self.addCleanup(setattr, images, "_render", real_render)

    def fake_render(self, ok=("01", "02", "03")):
        def render(script, beat, dest):
            self.rendered.append(beat.id)
            if beat.id not in ok:
                raise SystemExit(f"fal job for {beat.id} failed")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(b"png")
            return 3
        images._render = render

    def manifest(self):
        return json.loads(self.script.manifest_path.read_text(encoding="utf-8"))

    def test_every_beat_is_rendered_and_recorded(self):
        self.fake_render()
        result = images.generate(self.script)
        self.assertEqual(result["generated"], ["01", "02", "03"])
        self.assertEqual(sorted(self.manifest()["images"]), ["01", "02", "03"])

    def test_a_failed_beat_does_not_lose_the_ones_that_rendered(self):
        """Beats run in parallel, so a mid-run failure arrives while siblings
        are still in flight. If it took the run down with it, images already
        paid for would be missing from the manifest and re-rendered on the
        retry -- paid for twice."""
        self.fake_render(ok=("01", "03"))
        with self.assertRaises(SystemExit):
            images.generate(self.script)
        self.assertEqual(sorted(self.manifest()["images"]), ["01", "03"])

    def test_a_failed_run_says_which_beats_to_retry(self):
        """Silence here reads as success. The whole run must fail loud, and
        name the beats, because nothing downstream can tell a missing frame
        from one that was never asked for."""
        self.fake_render(ok=("01",))
        with self.assertRaises(SystemExit) as caught:
            images.generate(self.script)
        message = str(caught.exception)
        self.assertIn("failed for beats: 02, 03", message)
        self.assertIn("--only 02,03", message)

    def test_a_cached_beat_is_not_paid_for_again(self):
        """The hash is the whole reason assets/ is permanent: an unchanged
        prompt must never reach fal a second time."""
        self.fake_render()
        images.generate(self.script)
        self.rendered.clear()
        images.generate(self.script)
        self.assertEqual(self.rendered, [])

    def test_a_changed_prompt_invalidates_only_that_beat(self):
        """Editing one beat's prompt should re-render one frame, not the reel."""
        self.fake_render()
        images.generate(self.script)
        self.rendered.clear()
        self.script.beats[1].image_prompt = "a different marble"
        images.generate(self.script)
        self.assertEqual(self.rendered, ["02"])


if __name__ == "__main__":
    unittest.main()
