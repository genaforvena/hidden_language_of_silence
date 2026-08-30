#!/usr/bin/env python3
"""provenance.py — the block every artifact in this repo carries.

Extracted from silent_channel.py so there is exactly ONE implementation. The
extraction is not tidying: the stamp is keyed on THE INSTRUMENT'S OWN BYTES, and
`SCRIPT = os.path.abspath(__file__)` evaluated inside a shared module names the
SHARED module. A second script importing that would have attested this file's
sha256 while reporting its own numbers -- a provenance block naming the wrong
instrument is worse than none, because it reads as evidence.

So the script path is an ARGUMENT, taken once at import time by the caller.
"""

import datetime, hashlib, os, subprocess, sys


def _git(script, *args):
    try:
        p = subprocess.run(["git", "-C", os.path.dirname(script)] + list(args),
                           capture_output=True, text=True, timeout=15)
        return p.stdout.strip() if p.returncode == 0 else None
    except Exception:
        return None


def _script_sha(script):
    """sha256 of the source on disk. Read as early as possible: the interpreter has
    already loaded and compiled these bytes, so at import time this is what is
    running. Read it at write time instead and you hash whatever the file became."""
    try:
        with open(script, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception:
        return "unknown:script-unreadable"


def stamp(script):
    head = _git(script, "rev-parse", "HEAD")
    inst = _git(script, "status", "--porcelain", "--", script)
    tree = _git(script, "status", "--porcelain")
    return {
        "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "script_sha256": _script_sha(script),
        "git_head": head or "unknown:not-a-repo-or-git-failed",
        "instrument_dirty": None if inst is None else bool(inst.strip()),
        "tree_dirty_files": None if tree is None else len([l for l in tree.splitlines() if l.strip()]),
    }


class Instrument:
    """Holds the at-import stamp for ONE script and renders its provenance block."""

    def __init__(self, script):
        self.script = os.path.abspath(script)
        self.at_start = stamp(self.script)

    def block(self, argv, **extra):
        """Compares the start stamp against a fresh one so a mid-run edit of the
        instrument is ASSERTED, not merely absent."""
        now = stamp(self.script)
        # The verdict keys on the INSTRUMENT'S OWN BYTES, never on git_head. HEAD is a
        # property of the TREE: any commit anywhere in the repo moves it, and on a run
        # that takes hours that is a near-certainty. Keyed on HEAD this field would be
        # permanently true, therefore permanently ignored, and a REAL instrument change
        # would ride in under exactly that suppression.
        changed = [k for k in ("script_sha256", "instrument_dirty")
                   if self.at_start.get(k) != now.get(k)]
        tree_moved = self.at_start.get("git_head") != now.get("git_head")
        out = {
            "at_start": self.at_start,
            "at_write": now,
            "changed_mid_run": changed or False,
            "tree_moved_mid_run": tree_moved,   # context, never the alarm
            "note": ("the instrument changed under this run — at_start is what produced "
                     "these numbers" if changed else
                     "instrument identical at start and at write"
                     + (" (HEAD moved, but the instrument's own bytes did not)"
                        if tree_moved else "")),
            "argv": list(argv),
            "python": sys.version.split()[0],
        }
        out.update(extra)
        return out
