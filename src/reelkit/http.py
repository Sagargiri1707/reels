"""
Thin urllib helpers. Stdlib only, so the pipeline needs no pip install.

Errors are raised with the response body attached -- fal and fish both put
the useful part of a failure in the body, not the status line.
"""

import json
import time
import urllib.error
import urllib.request


class HttpError(RuntimeError):
    def __init__(self, status, url, body):
        self.status = status
        self.url = url
        self.body = body
        super().__init__(f"HTTP {status} from {url}\n{body[:1500]}")


def _open(req, timeout):
    try:
        return urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        raise HttpError(e.code, req.full_url, body) from None


def post_json(url, payload, headers, timeout=180):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    with _open(req, timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def get_json(url, headers, timeout=60):
    req = urllib.request.Request(url, headers=headers, method="GET")
    with _open(req, timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def download(url, dest, timeout=180):
    req = urllib.request.Request(url, method="GET")
    with _open(req, timeout) as r:
        data = r.read()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return len(data)


def stream_sse(url, payload, headers, timeout=600):
    """
    POST a JSON body and yield each decoded `data:` event as a dict.

    Server-sent events are `field: value` lines terminated by a blank line.
    Only `data:` carries anything we need, and both APIs send one JSON object
    per event, so multi-line data frames are joined before parsing.
    """
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    with _open(req, timeout) as r:
        buf = []
        for raw in r:
            line = raw.decode("utf-8", "replace").rstrip("\r\n")
            if line == "":
                if buf:
                    chunk = "".join(buf)
                    buf = []
                    if chunk and chunk != "[DONE]":
                        try:
                            yield json.loads(chunk)
                        except json.JSONDecodeError:
                            continue
                continue
            if line.startswith("data:"):
                buf.append(line[5:].lstrip())
        if buf:
            chunk = "".join(buf)
            if chunk and chunk != "[DONE]":
                try:
                    yield json.loads(chunk)
                except json.JSONDecodeError:
                    pass


def poll(fn, is_done, interval=2.0, limit=600, label="job"):
    """Call fn() until is_done(result), or give up loudly."""
    waited = 0.0
    while True:
        result = fn()
        if is_done(result):
            return result
        if waited >= limit:
            raise SystemExit(f"{label} did not finish within {limit:.0f}s")
        time.sleep(interval)
        waited += interval
