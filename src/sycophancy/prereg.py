"""Prereg-tag guard. Confirmatory scripts call require_prereg_tag() so they
refuse to run before the pre-registration is frozen at Git tag prereg-v0.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _git_tag_exists(tag: str) -> bool:
    try:
        out = subprocess.run(
            ["git", "tag", "-l", tag],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
    return out.stdout.strip() == tag


def require_prereg_tag(tag: str = "prereg-v0") -> None:
    """Sys.exit with a clear message if `tag` is not present in the repo."""
    if _git_tag_exists(tag):
        return
    sys.stderr.write(
        f"ERROR: pre-registration tag {tag!r} not found in repository.\n"
        f"This script implements a confirmatory analysis. The pre-registration\n"
        f"in prereg/PRE_REGISTRATION.md must be reviewed and frozen at the tag\n"
        f"{tag!r} BEFORE any of H1-H5 results are computed. To freeze:\n\n"
        f"    make tag-prereg\n\n"
        f"After tagging, re-run this script.\n"
    )
    sys.exit(2)
