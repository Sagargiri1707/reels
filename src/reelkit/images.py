"""
Generate one image per beat with fal (openai/gpt-image-2) into assets/.

assets/ is permanent. Every file in it cost money, so a beat is only
regenerated when its prompt actually changed, or when --force is passed.
The manifest records the hash that decision is based on.
"""

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from .config import FAL_QUEUE, require_env
from .http import get_json, post_json, poll, download


def _headers():
    return {"Authorization": f"Key {require_env('FAL_KEY')}"}


def prompt_hash(script, beat):
    """Identity of a rendered image: the prompt plus everything that changes
    how it is drawn. Change any of these and the cached png is stale."""
    payload = json.dumps({
        "prompt": script.prompt_for(beat),
        "model": script.image["model"],
        "image_size": script.image["image_size"],
        "quality": script.image["quality"],
        "output_format": script.image.get("output_format", "png"),
    }, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def read_manifest(script):
    if not script.manifest_path.exists():
        return {}
    try:
        return json.loads(script.manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def write_manifest(script, manifest):
    script.manifest_path.parent.mkdir(parents=True, exist_ok=True)
    script.manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _submit(script, prompt):
    model = script.image["model"]
    body = {
        "prompt": prompt,
        "image_size": script.image["image_size"],
        "quality": script.image["quality"],
        "output_format": script.image.get("output_format", "png"),
        "num_images": 1,
    }
    return post_json(f"{FAL_QUEUE}/{model}", body, _headers())


def _await_result(script, submitted):
    model = script.image["model"]
    request_id = submitted.get("request_id")
    if not request_id:
        raise SystemExit(f"fal did not return a request_id: {submitted}")

    status_url = submitted.get("status_url") or \
        f"{FAL_QUEUE}/{model}/requests/{request_id}/status"
    response_url = submitted.get("response_url") or \
        f"{FAL_QUEUE}/{model}/requests/{request_id}"

    def check():
        return get_json(status_url, _headers())

    def done(s):
        status = s.get("status")
        if status in ("FAILED", "ERROR"):
            raise SystemExit(f"fal job {request_id} failed: {s}")
        return status == "COMPLETED"

    poll(check, done, interval=2.0, limit=600, label=f"fal job {request_id}")
    return get_json(response_url, _headers())


def _image_url(result):
    images = result.get("images") or []
    if not images:
        raise SystemExit(f"fal returned no images: {result}")
    url = images[0].get("url")
    if not url:
        raise SystemExit(f"fal image has no url: {images[0]}")
    return url


def _render(script, beat, dest):
    """Submit, wait, download. Runs on a worker thread, so it touches nothing
    shared -- the manifest is written by the caller, on the main thread."""
    result = _await_result(script, _submit(script, script.prompt_for(beat)))
    return download(_image_url(result), dest)


def generate(script, force=False, only=None):
    """
    Ensure every beat has an image on disk. Returns a summary dict.

    `only` is an optional set of beat ids, for re-rolling a single frame.

    Beats are rendered concurrently: each one is an independent fal job, and
    the time is spent almost entirely waiting in that queue. A beat that fails
    does not cancel the others -- everything that lands is written to the
    manifest and kept, and the failures are raised together at the end, so a
    retry re-renders only what is actually missing.
    """
    script.assets_dir.mkdir(parents=True, exist_ok=True)
    manifest = read_manifest(script)
    images = manifest.setdefault("images", {})

    todo, skipped = [], []
    for beat in script.beats:
        if only and beat.id not in only:
            continue

        dest = script.image_path(beat)
        want = prompt_hash(script, beat)
        have = (images.get(beat.id) or {}).get("hash")

        if dest.exists() and have == want and not force:
            skipped.append(beat.id)
            print(f"  skip  {beat.id}  {dest.name}")
            continue

        todo.append((beat, dest, want))

    made, failed = [], []
    workers = max(1, int(script.image.get("concurrency") or 1))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        jobs = {}
        for beat, dest, want in todo:
            print(f"  gen   {beat.id}  {beat.image_prompt[:56]}")
            jobs[pool.submit(_render, script, beat, dest)] = (beat, dest, want)

        for job in as_completed(jobs):
            beat, dest, want = jobs[job]
            try:
                size = job.result()
            except (Exception, SystemExit) as e:
                failed.append(beat.id)
                print(f"  FAIL  {beat.id}  {e}")
                continue

            images[beat.id] = {"hash": want, "file": dest.name, "bytes": size}
            write_manifest(script, manifest)   # after each beat, so a crash
            made.append(beat.id)               # does not lose what was paid for
            print(f"  ok    {beat.id}  {dest.name}")

    made.sort()
    print(f"images: {len(made)} generated, {len(skipped)} cached"
          + (f", {len(failed)} FAILED" if failed else ""))
    if failed:
        raise SystemExit(
            "image generation failed for beats: " + ", ".join(sorted(failed)) +
            f"\nwhat rendered is kept; re-run to retry only those:"
            f"\n  python3 reel.py images {script.path.name} "
            f"--only {','.join(sorted(failed))}")
    return {"generated": made, "skipped": skipped}


def verify(script):
    """Fail loud if the stitcher would hit a missing frame."""
    missing = [b.id for b in script.beats if not script.image_path(b).exists()]
    if missing:
        raise SystemExit(
            "missing images for beats: " + ", ".join(missing) +
            f"\nrun: python3 reel.py images {script.path.name}"
        )
