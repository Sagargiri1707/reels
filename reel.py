#!/usr/bin/env python3
"""Entry point, so the package runs with no install step."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from reelkit.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
