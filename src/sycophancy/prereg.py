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
    prereg_file = {
        "prereg-v0": "prereg/PRE_REGISTRATION.md",
        "prereg-v1": "prereg/PRE_REGISTRATION_v1.md",
    }.get(tag, "prereg/PRE_REGISTRATION.md")
    sys.stderr.write(
        f"ERROR: pre-registration tag {tag!r} not found in repository.\n"
        f"This script implements a confirmatory analysis. The pre-registration\n"
        f"in {prereg_file} must be reviewed and frozen at the tag\n"
        f"{tag!r} BEFORE any confirmatory results are computed. To freeze:\n\n"
        f"    git add prereg/ src/ scripts/ docs/AMENDMENTS.md\n"
        f"    git commit -m 'Freeze {tag} pre-registration'\n"
        f"    git tag {tag}\n\n"
        f"After tagging, re-run this script.\n"
    )
    sys.exit(2)


def require_prereg_v1() -> None:
    """Convenience guard for the v1 factorial analysis family (H6/H7/H8)."""
    require_prereg_tag("prereg-v1")
