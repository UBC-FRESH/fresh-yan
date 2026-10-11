"""Record provenance helpers.

Every tracked record carries the provenance of the code and libraries that produced it:
``fy_commit`` (git commit of this repository, ``+dirty`` when the working tree was
modified), ``fy_version``, ``ws3_version``, and ``libcbm_version``.
"""

from __future__ import annotations

import subprocess

import pandas as pd

from . import __version__


def git_commit() -> str:
    """Short git commit of the current checkout (``+dirty`` if ``src/`` is modified)."""
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        dirty = subprocess.run(
            ["git", "status", "--porcelain", "src/"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        return commit + ("+dirty" if dirty else "")
    except Exception:
        return "unknown"


def provenance() -> dict[str, str]:
    """Provenance metadata for a record produced by the current environment."""
    import libcbm
    import ws3

    return {
        "fy_commit": git_commit(),
        "fy_version": __version__,
        "ws3_version": getattr(ws3, "__version__", "unknown"),
        "libcbm_version": getattr(libcbm, "__version__", "unknown"),
    }


def with_provenance(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of ``df`` with provenance columns appended."""
    out = df.copy()
    for key, value in provenance().items():
        out[key] = value
    return out
