"""
Publish a finished post to Instagram through Meta's Content Publishing API.

There is no scheduling endpoint. Meta Business Suite's planner is a UI surface
with no public API behind it, and `POST /{ig-user-id}/media` has no
`publish_time` / `scheduled_publish_time` parameter -- only Facebook *Page*
posts get those. So scheduling lives in this repo: schedule.py keeps a queue
and calls publish_dir() when an entry falls due.

Two shapes of post, two upload paths, because Meta is not symmetric here:

  reel      one mp4. Uploaded straight off disk with the resumable protocol,
            so the video never needs to be hosted anywhere public.
  carousel  several pngs. Images can ONLY be handed over as a URL, so each
            frame is pushed somewhere public first -- see _publicise().

Every call is two-phase: build a container, then publish it. A container that
is never published expires after 24 hours.
"""

import os
import subprocess
import time
from pathlib import Path

from . import http
from .config import ROOT, load_dotenv

# v26.0 shipped 2026-07-29. Meta supports a version for ~2 years, so pinning is
# safer than tracking `latest` -- an unpinned call breaks on their schedule.
API_VERSION = "v26.0"

# graph.facebook.com is the Facebook-Login path (token from a Page-linked
# business app), which is what you get if the account already lives in
# Business Suite. graph.instagram.com is the Instagram-Login path. Same
# endpoints either way.
DEFAULT_HOST = "https://graph.facebook.com"
UPLOAD_HOST = "https://rupload.facebook.com/ig-api-upload"

# The container has to finish transcoding before it can be published.
STATUS_INTERVAL = 5.0
STATUS_LIMIT = 900.0


class PublishError(RuntimeError):
    pass


# --------------------------------------------------------------------------
# credentials + transport


def _creds():
    load_dotenv()
    token = os.environ.get("IG_ACCESS_TOKEN")
    user_id = os.environ.get("IG_USER_ID")
    if not token or not user_id:
        raise SystemExit(
            "IG_ACCESS_TOKEN and IG_USER_ID must be set. Put them in "
            f"{ROOT / '.env'} or export them."
        )
    host = os.environ.get("IG_API_HOST", DEFAULT_HOST).rstrip("/")
    return token, user_id, host


def _post(path, payload):
    token, _, host = _creds()
    url = f"{host}/{API_VERSION}/{path}"
    return http.post_json(url, {**payload, "access_token": token}, headers={})


def _get(path, fields):
    token, _, host = _creds()
    url = f"{host}/{API_VERSION}/{path}?fields={fields}&access_token={token}"
    return http.get_json(url, headers={})


# --------------------------------------------------------------------------
# hosting images


def _publicise(path):
    """
    Copy one local file somewhere Meta can fetch it, and return that URL.

    Deliberately a shell template rather than a baked-in S3 client: the repo
    is stdlib-only, and whatever already moves files for you (aws, rclone,
    scp, wrangler) is a better answer than a signing implementation here.

        MEDIA_UPLOAD_CMD=aws s3 cp {src} s3://bucket/ig/{name} --acl public-read
        MEDIA_PUBLIC_URL=https://bucket.s3.amazonaws.com/ig/{name}
    """
    load_dotenv()
    cmd = os.environ.get("MEDIA_UPLOAD_CMD")
    url_tpl = os.environ.get("MEDIA_PUBLIC_URL")
    if not cmd or not url_tpl:
        raise SystemExit(
            "Carousel images have to be publicly fetchable -- Meta's image "
            "endpoint takes a URL and nothing else. Set MEDIA_UPLOAD_CMD and "
            f"MEDIA_PUBLIC_URL in {ROOT / '.env'}."
        )
    fields = {"src": str(path), "name": path.name}
    subprocess.run(cmd.format(**fields), shell=True, check=True)
    return url_tpl.format(**fields)


# --------------------------------------------------------------------------
# containers


def _wait_finished(container_id):
    """Block until the container transcodes, or fail with Meta's own reason."""

    def check():
        return _get(container_id, "status_code,status")

    result = http.poll(
        check,
        lambda r: r.get("status_code") in ("FINISHED", "ERROR", "EXPIRED", "PUBLISHED"),
        interval=STATUS_INTERVAL,
        limit=STATUS_LIMIT,
        label=f"container {container_id}",
    )
    code = result.get("status_code")
    if code not in ("FINISHED", "PUBLISHED"):
        raise PublishError(
            f"container {container_id} is {code}: {result.get('status', '')}"
        )
    return container_id


def reel_container(video, caption, share_to_feed=True, cover=None):
    """
    Create a REELS container and push the mp4 into it from disk.

    upload_type=resumable is what makes the local path work -- without it the
    container demands a public video_url.
    """
    token, user_id, _ = _creds()
    payload = {
        "media_type": "REELS",
        "upload_type": "resumable",
        "caption": caption,
        "share_to_feed": share_to_feed,
    }
    if cover:
        payload["cover_url"] = _publicise(Path(cover))
    container_id = _post(f"{user_id}/media", payload)["id"]

    data = Path(video).read_bytes()
    http.post_bytes(
        f"{UPLOAD_HOST}/{API_VERSION}/{container_id}",
        data,
        headers={
            "Authorization": f"OAuth {token}",
            "offset": "0",
            "file_size": str(len(data)),
        },
    )
    return _wait_finished(container_id)


def carousel_container(images, caption):
    """
    Create one child container per image, then the parent that binds them.

    Children carry no caption -- only the parent does. Meta caps a carousel at
    10 items and rejects the whole post if one child is short.
    """
    _, user_id, _ = _creds()
    images = list(images)
    if not 2 <= len(images) <= 10:
        raise PublishError(
            f"a carousel needs 2-10 images, got {len(images)}"
        )
    children = []
    for image in images:
        child = _post(f"{user_id}/media", {
            "image_url": _publicise(Path(image)),
            "is_carousel_item": True,
        })["id"]
        children.append(_wait_finished(child))

    parent = _post(f"{user_id}/media", {
        "media_type": "CAROUSEL",
        "children": ",".join(children),
        "caption": caption,
    })["id"]
    return _wait_finished(parent)


def publish_container(container_id):
    _, user_id, _ = _creds()
    result = _post(f"{user_id}/media_publish", {"creation_id": container_id})
    media_id = result.get("id")
    if not media_id:
        raise PublishError(f"no media id came back: {result}")
    return media_id


def quota():
    """Posts already published in the rolling 24h window. The cap is 100."""
    _, user_id, _ = _creds()
    data = _get(f"{user_id}/content_publishing_limit", "quota_usage,config")
    row = (data.get("data") or [{}])[0]
    return row.get("quota_usage", 0), (row.get("config") or {}).get("quota_total", 100)


# --------------------------------------------------------------------------
# one finished output directory -> one post


def read_post(directory):
    """
    Work out what is in an out/ directory: (kind, media, caption).

    The pipeline already writes exactly one mp4 for a reel and a numbered set
    of pngs for a carousel, so the shape of the directory is the answer -- no
    extra metadata file to keep in sync.
    """
    directory = Path(directory)
    if not directory.is_dir():
        raise SystemExit(f"not a directory: {directory}")

    caption_file = directory / "post.txt"
    caption = caption_file.read_text(encoding="utf-8").strip() if caption_file.exists() else ""

    videos = sorted(directory.glob("*.mp4"))
    if videos:
        return "reel", videos[0], caption

    # Sorted, because slide order is the post: -01, -02, -03...
    images = sorted(directory.glob("*.png"))
    if images:
        return "carousel", images, caption

    raise SystemExit(f"no mp4 and no png in {directory}")


def publish_dir(directory, dry_run=False, share_to_feed=True):
    """Publish a finished out/ directory. Returns the new media id."""
    kind, media, caption = read_post(directory)

    if dry_run:
        shown = media if kind == "reel" else "\n    ".join(str(p) for p in media)
        print(f"  {kind} from {directory}")
        print(f"    {shown}")
        print(f"    caption: {caption[:70]}{'...' if len(caption) > 70 else ''}")
        return None

    used, total = quota()
    if used >= total:
        raise PublishError(
            f"already published {used}/{total} in the last 24h -- Meta will reject this"
        )

    if kind == "reel":
        container_id = reel_container(media, caption, share_to_feed=share_to_feed)
    else:
        container_id = carousel_container(media, caption)

    # Meta returns FINISHED slightly before the media is really publishable
    # often enough that a bare retry here saves a whole scheduled slot.
    for attempt in range(3):
        try:
            return publish_container(container_id)
        except http.HttpError:
            if attempt == 2:
                raise
            time.sleep(15)
