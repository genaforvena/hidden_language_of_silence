#!/usr/bin/env python3
"""Regression test for the provenance stamp.

The defect this guards is not hypothetical: result-msg2.json, the replication that
reverses run 1's ordering, was written by a process launched before the commit that
added the per-position breakdown. It ran the old code to completion and its only
trace was a MISSING KEY — indistinguishable from a run with nothing to report.

The arm that matters is the RED one. A stamp taken only at write time passes every
naive check and still records the wrong commit, so the test drives a real mid-run
edit in a scratch clone and asserts that `at_start` holds what actually ran.

Run: python3 measure/test_provenance.py
"""
import json, os, random, re, string, subprocess, sys, tempfile, textwrap, time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
FAILS = []


def check(name, ok, detail=""):
    print(f"  {'ok  ' if ok else 'FAIL'}  {name}{'  — ' + detail if detail else ''}")
    if not ok:
        FAILS.append(name)


def write_relay(path, delay=0.0):
    """A reader stand-in: emits a word of each requested length. Not a model — it
    exists so this test costs no inference. `delay` widens the run so a mid-run edit
    can actually land; without it the run finishes first and the RED arm goes green,
    which is an experiment that never ran rather than a passing test."""
    with open(path, "w") as f:
        f.write(textwrap.dedent(f'''\
            #!/usr/bin/env python3
            import sys, random, re, string, time
            time.sleep({delay})
            p = sys.argv[1]
            if "common English words" in p:
                print("\\n".join("".join(random.choice(string.ascii_lowercase)
                      for _ in range(random.randint(1, 12))) for _ in range(240)))
                sys.exit()
            lens = [int(x) for x in re.search(r"Word lengths, in order: ([\\d ]+)", p).group(1).split()]
            print(" ".join("".join(random.choice("abcde") for _ in range(n)) for n in lens))
        '''))
    os.chmod(path, 0o755)


def run(cwd, relay, out, n=4, bg=False):
    cmd = [sys.executable, "measure/silent_channel.py", "--relay", relay,
           "-n", str(n), "--no-embed", "--out", out]
    if bg:
        return subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=600)


def git(cwd, *a):
    return subprocess.run(["git", "-C", cwd] + list(a), capture_output=True, text=True)


def clone(dst):
    subprocess.run(["git", "clone", "-q", REPO, dst], check=True, capture_output=True)
    # The working copy may be ahead of HEAD; test the instrument as it stands on disk.
    #
    # EVERY tracked .py in the repository, not a named file. This has now been widened
    # twice, for the same reason each time, and the reason is worth keeping: the
    # "instrument" is whatever the run imports, and that set GROWS. It was one file until
    # the provenance block moved into measure/provenance.py; it reached outside measure/
    # entirely when silent_channel.py started importing the repo-root silent.py. Each
    # time, a narrower copy left the working-tree script running against COMMITTED
    # helpers -- a hybrid that exists nowhere, reported as "the instrument on disk".
    #
    # A brand-new helper is the loud case (ImportError). A helper merely EDITED is the
    # quiet one, and it is what this guards: the second widening was forced by an
    # AttributeError, i.e. by luck, on a change that could as easily have been silent.
    root = os.path.dirname(HERE)
    tracked = subprocess.run(["git", "-C", root, "ls-files", "--cached", "--others", "--exclude-standard", "*.py"],
                             capture_output=True, text=True).stdout.split()
    for rel in tracked:
        src = os.path.join(root, rel)
        if not os.path.exists(src):
            continue
        os.makedirs(os.path.dirname(os.path.join(dst, rel)) or dst, exist_ok=True)
        subprocess.run(["cp", src, os.path.join(dst, rel)], check=True)
    git(dst, "add", "-A")
    git(dst, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "baseline")
    return git(dst, "rev-parse", "HEAD").stdout.strip()


def main():
    with tempfile.TemporaryDirectory() as tmp:
        relay = os.path.join(tmp, "relay")

        # ---- GREEN ARM: an undisturbed run agrees with itself ------------------
        d1 = os.path.join(tmp, "clean")
        head = clone(d1)
        write_relay(relay)
        out1 = os.path.join(tmp, "clean.json")
        run(d1, relay, out1)
        d = json.load(open(out1))
        check("the artifact carries a provenance block at all", "provenance" in d,
              "absent — a result file that cannot name its instrument is not evidence")
        if "provenance" not in d:
            print("\nFAILED: no provenance block; remaining arms cannot run")
            sys.exit(1)
        p = d["provenance"]
        check("undisturbed run: changed_mid_run is False", p["changed_mid_run"] is False,
              repr(p["changed_mid_run"]))
        check("undisturbed run: at_start names the real HEAD",
              p["at_start"]["git_head"] == head, p["at_start"]["git_head"][:12])
        check("undisturbed run: instrument_dirty is False",
              p["at_start"]["instrument_dirty"] is False)
        check("undisturbed run: sha256 is a real digest",
              bool(re.fullmatch(r"[0-9a-f]{64}", p["at_start"]["script_sha256"])))

        # ---- RED ARM: the defect itself, reproduced ----------------------------
        # This is the arm the whole block exists for. If it goes green, check that
        # the run actually outlived the edit before believing it.
        d2 = os.path.join(tmp, "edited")
        head_before = clone(d2)
        write_relay(relay, delay=0.25)
        out2 = os.path.join(tmp, "edited.json")
        proc = run(d2, relay, out2, n=10, bg=True)
        time.sleep(3.0)
        edited_while_running = proc.poll() is None
        with open(os.path.join(d2, "measure", "silent_channel.py"), "a") as f:
            f.write("\n# an edit landed while the run was in flight\n")
        git(d2, "add", "-A")
        git(d2, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "mid-run edit")
        head_after = git(d2, "rev-parse", "HEAD").stdout.strip()
        proc.wait(timeout=600)

        check("RED ARM IS VALID: the edit landed while the run was still in flight",
              edited_while_running,
              "run finished before the edit — this arm proved nothing" if not edited_while_running else "")
        check("the two commits differ", head_before != head_after)

        p = json.load(open(out2))["provenance"]
        check("mid-run edit is DETECTED, not silent", bool(p["changed_mid_run"]),
              repr(p["changed_mid_run"]))
        check("at_start names the commit that ACTUALLY RAN",
              p["at_start"]["git_head"] == head_before, p["at_start"]["git_head"][:12])
        check("at_write names the commit that landed",
              p["at_write"]["git_head"] == head_after, p["at_write"]["git_head"][:12])
        # The point of the whole design, stated as an assertion: a write-time-only
        # stamp would have put head_after in the file — the commit that never ran.
        check("a WRITE-TIME-ONLY stamp would have been WRONG here",
              p["at_write"]["git_head"] != head_before,
              "write-time would record " + p["at_write"]["git_head"][:12] + ", which did not run")
        check("the shas differ too", p["at_start"]["script_sha256"] != p["at_write"]["script_sha256"])

        # ---- BOUNDING ARM: an UNRELATED commit is not an instrument change ------
        # This arm did not exist in the first version and that is exactly why the
        # false positive shipped: the only mutation ever driven was the one that
        # edits the instrument itself, so the test could confirm the alarm but never
        # bound it. Keyed on git_head, this arm goes red — and on a run of any
        # length an unrelated commit is near-certain, so the field would be
        # permanently true and therefore permanently ignored.
        d3 = os.path.join(tmp, "unrelated")
        head_b = clone(d3)
        write_relay(relay, delay=0.25)
        out3 = os.path.join(tmp, "unrelated.json")
        proc = run(d3, relay, out3, n=10, bg=True)
        time.sleep(3.0)
        still_running = proc.poll() is None
        with open(os.path.join(d3, "UNRELATED.md"), "w") as f:
            f.write("a commit that does not touch the instrument\n")
        git(d3, "add", "-A")
        git(d3, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "unrelated commit")
        head_a = git(d3, "rev-parse", "HEAD").stdout.strip()
        proc.wait(timeout=600)

        check("BOUNDING ARM IS VALID: the unrelated commit landed mid-run",
              still_running and head_b != head_a)
        p = json.load(open(out3))["provenance"]
        check("an unrelated commit is NOT reported as an instrument change",
              p["changed_mid_run"] is False, repr(p["changed_mid_run"]))
        check("the instrument's own bytes are unchanged across it",
              p["at_start"]["script_sha256"] == p["at_write"]["script_sha256"])
        check("the HEAD move is still reported, as context",
              p.get("tree_moved_mid_run") is True, repr(p.get("tree_moved_mid_run")))
        check("and the note says so rather than crying instrument change",
              "instrument's own bytes did not" in p["note"], p["note"])

        # ---- the recovery metric names its own direction -----------------------
        src = open(os.path.join(HERE, "silent_channel.py")).read()
        check("recovery block declares metric and direction",
              '"metric": "cosine_similarity"' in src and '"direction": "higher = closer' in src)

    print()
    if FAILS:
        print(f"FAILED: {len(FAILS)} — " + ", ".join(FAILS))
        sys.exit(1)
    print("all arms green (including the red arm going red)")


if __name__ == "__main__":
    main()
