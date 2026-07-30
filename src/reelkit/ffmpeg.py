"""ffmpeg / ffprobe process helpers."""

import shutil
import subprocess
import sys


def require_tools():
    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            raise SystemExit(f"{tool} not found on PATH -- brew install ffmpeg")


def run(cmd):
    """Run a command, raise with useful output on failure."""
    p = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if p.returncode != 0:
        sys.stderr.write("\n$ " + " ".join(str(c) for c in cmd) + "\n")
        sys.stderr.write((p.stderr or "")[-4000:] + "\n")
        raise SystemExit(f"command failed ({p.returncode})")
    return p.stdout


def has_filter(name):
    """True if this ffmpeg build actually ships the filter. Slimmed builds
    drop libass, and the failure otherwise surfaces as an unreadable
    filtergraph parse error deep in the final mux."""
    out = subprocess.run(["ffmpeg", "-hide_banner", "-filters"],
                         capture_output=True, text=True).stdout
    return any(line.split()[1:2] == [name]
               for line in out.splitlines() if line.strip())


def require_captions():
    if has_filter("ass"):
        return
    raise SystemExit(
        "this ffmpeg was built without libass, so captions cannot be burned in.\n"
        "  check:  ffmpeg -version | grep -o enable-libass\n"
        "  fix:    brew reinstall ffmpeg\n"
        "  or:     render without captions using --no-captions"
    )


def probe_duration(path):
    out = run([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(path),
    ])
    return float(out.strip())
