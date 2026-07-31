#!/usr/bin/env python3
"""Empirical screening for the Markdig 30-case experiment.

Screens one category queue (S, P, or N) strictly in seeded order, front to
back, accepting the first candidates whose executable conditions hold, until
MAX_ACCEPT are accepted or the queue is exhausted.

Executable acceptance conditions (frozen in protocol.md):
  S: base build OK; base full suite green; discovered target filter green and
     non-empty at base; production-source-only diff applied; build OK; same
     target filter red.
  P: base build OK; base full suite green; test-oracle diff (test .cs + spec
     .md, never *.generated.cs) applied; build OK; discovered target filter
     red; production-source diff added; build OK; same filter green; full
     suite green.
  N: base build OK; base full suite green; production-source diff applied;
     build OK; full suite green.

Selection failures (candidate unsuitable) are recorded as status=rejected with
a reason; tool/pipeline failures as status=pipeline_error (one retry first).

Usage: python3 screen.py <repo-root> <exp-dir> <category>
"""

import json
import os
import re
import shutil
import subprocess
import sys

MAX_ACCEPT = 10
BUILD_TIMEOUT = 900
TEST_TIMEOUT = 900

CLASS_RE = re.compile(r"\bclass\s+([A-Za-z_]\w*)")
SUMMARY_RE = re.compile(
    r"Failed:\s*(\d+),\s*Passed:\s*(\d+),\s*Skipped:\s*(\d+),\s*Total:\s*(\d+)")
FAILED_NAME_RE = re.compile(r"^\s*Failed\s+(\S+)", re.MULTILINE)


class Pipeline(Exception):
    pass


class Reject(Exception):
    pass


def load_metadata(exp_dir):
    path = os.path.join(exp_dir, "metadata", "experiment.json")
    with open(path) as f:
        return path, json.load(f)


def sh(cmd, cwd, env=None, timeout=None, stdin_text=None):
    try:
        r = subprocess.run(cmd, cwd=cwd, env=env, input=stdin_text,
                           capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as e:
        raise Pipeline(f"timeout: {' '.join(cmd)}") from e
    return r


class Screener:
    def __init__(self, repo, exp_dir, entry, category):
        self.repo = os.path.abspath(repo)
        self.exp_dir = os.path.abspath(exp_dir)
        self.e = entry
        self.cat = category
        self.qid = entry["queue_id"]
        self.wt = os.path.join(self.repo, ".worktrees", f"screen-{self.qid}")
        self.case_dir = os.path.join(self.exp_dir, "screening", self.qid)
        self.log_dir = os.path.join(self.case_dir, "logs")
        self.record = {
            "queue_id": self.qid,
            "category": category,
            "upstream_sha": entry["sha"],
            "base_sha": entry["parent"],
            "subject": entry["subject"],
            "date": entry["date"],
            "prod_src_files": entry["prod_src_files"],
            "test_src_files": entry["test_src_files"],
            "spec_md_files": entry["spec_md_files"],
            "generated_files_in_commit": entry["generated_files"],
            "construction": [],
            "runs": [],
            "tfm": None,
            "dotnet_sdk": None,
            "target_filter": None,
            "status": None,
            "reason": None,
        }
        self.log_seq = 0

    # -- infra ------------------------------------------------------------
    def env(self):
        home = os.path.expanduser("~")
        env = dict(os.environ)
        env.update({
            "DOTNET_ROOT": f"{home}/.dotnet",
            "PATH": f"{home}/.dotnet:{env.get('PATH', '')}",
            "DOTNET_CLI_TELEMETRY_OPTOUT": "1",
            "DOTNET_NOLOGO": "1",
            "DOTNET_CLI_UI_LANGUAGE": "en",
        })
        return env

    def sanitize(self, text):
        home = os.path.expanduser("~")
        return (text.replace(self.wt, "<worktree>")
                    .replace(self.repo, "<repo>")
                    .replace(home, "<home>"))

    def save_log(self, name, text, tail=None):
        os.makedirs(self.log_dir, exist_ok=True)
        lines = self.sanitize(text).splitlines()
        if tail and len(lines) > tail:
            lines = [f"[... truncated, last {tail} lines ...]"] + lines[-tail:]
        self.log_seq += 1
        fname = f"{self.log_seq:02d}-{name}.txt"
        with open(os.path.join(self.log_dir, fname), "w") as f:
            f.write("\n".join(lines) + "\n")
        return fname

    def make_worktree(self):
        subprocess.run(["git", "-C", self.repo, "worktree", "remove", "--force", self.wt],
                       capture_output=True)
        r = sh(["git", "-C", self.repo, "worktree", "add", "--detach", self.wt,
                self.e["parent"]], cwd=self.repo)
        if r.returncode != 0:
            raise Pipeline(f"worktree-add-failed: {r.stderr.strip()[:200]}")
        gj = json.load(open(os.path.join(self.wt, "src", "global.json")))
        ver = gj["sdk"]["version"]
        self.record["tfm"] = "net10.0" if ver.startswith("10.") else "net9.0"
        r = sh(["dotnet", "--version"], cwd=os.path.join(self.wt, "src"), env=self.env())
        self.record["dotnet_sdk"] = r.stdout.strip()

    def drop_worktree(self):
        subprocess.run(["git", "-C", self.repo, "worktree", "remove", "--force", self.wt],
                       capture_output=True)

    def apply_diff(self, paths, label):
        diff = sh(["git", "-C", self.repo, "diff", "--no-renames",
                   self.e["parent"], self.e["sha"], "--", *paths], cwd=self.repo)
        if diff.returncode != 0:
            raise Pipeline(f"diff-extract-failed:{label}")
        for p in paths:
            if p.endswith(".generated.cs"):
                raise Pipeline(f"generated-file-in-apply-set:{label}")
        r = sh(["git", "-C", self.wt, "apply", "--whitespace=nowarn", "-"],
               cwd=self.wt, stdin_text=diff.stdout)
        self.record["construction"].append({
            "step": label,
            "command": f"git diff --no-renames {self.e['parent'][:12]} "
                       f"{self.e['sha'][:12]} -- <paths> | git -C <worktree> apply -",
            "paths": paths,
            "rc": r.returncode,
        })
        if r.returncode != 0:
            raise Pipeline(f"diff-apply-failed:{label}: {r.stderr.strip()[:200]}")

    def build(self, label, reject_reason):
        cmd = ["dotnet", "build", "src/Markdig.Tests/Markdig.Tests.csproj",
               "-c", "Release", "-f", self.record["tfm"], "-v", "q"]
        r = sh(cmd, cwd=self.wt, env=self.env(), timeout=BUILD_TIMEOUT)
        ok = r.returncode == 0
        log = self.save_log(f"build-{label}", r.stdout + r.stderr,
                            tail=None if ok else 60)
        self.record["runs"].append({"kind": "build", "label": label,
                                    "command": " ".join(cmd), "rc": r.returncode,
                                    "log": log})
        if not ok:
            raise Reject(reject_reason)

    def test(self, label, filt=None):
        cmd = ["dotnet", "test", "src/Markdig.Tests/Markdig.Tests.csproj",
               "-c", "Release", "-f", self.record["tfm"], "--no-build"]
        if filt:
            cmd += ["--filter", filt]
        r = sh(cmd, cwd=self.wt, env=self.env(), timeout=TEST_TIMEOUT)
        out = r.stdout + r.stderr
        m = SUMMARY_RE.search(out)
        if not m:
            if "No test matches" in out or "No test is available" in out:
                counts = {"failed": 0, "passed": 0, "skipped": 0, "total": 0}
            else:
                self.save_log(f"test-{label}", out, tail=120)
                raise Pipeline(f"unparseable-test-output:{label}")
        else:
            counts = dict(zip(("failed", "passed", "skipped", "total"),
                              map(int, m.groups())))
        failed_names = sorted(set(FAILED_NAME_RE.findall(out)))
        log = self.save_log(f"test-{label}", out,
                            tail=120 if counts["failed"] else 20)
        self.record["runs"].append({
            "kind": "test", "label": label, "command": " ".join(cmd),
            "filter": filt, "rc": r.returncode, "counts": counts,
            "failed_tests": failed_names[:50], "log": log})
        return counts

    # -- filter discovery -------------------------------------------------
    def discover_classes(self, rev):
        names = []
        for f in self.e["test_src_files"]:
            src = subprocess.run(["git", "-C", self.repo, "show", f"{rev}:{f}"],
                                 capture_output=True, text=True)
            if src.returncode == 0:
                names += CLASS_RE.findall(src.stdout)
        for f in self.e["spec_md_files"]:
            gen = f[:-3] + ".generated.cs"
            src = subprocess.run(["git", "-C", self.repo, "show", f"{rev}:{gen}"],
                                 capture_output=True, text=True)
            if src.returncode == 0:
                names += CLASS_RE.findall(src.stdout)
        return sorted(set(names))

    def set_filter(self, rev):
        names = self.discover_classes(rev)
        if not names:
            raise Reject("filter-undiscoverable")
        self.record["target_filter"] = "|".join(
            f"FullyQualifiedName~{n}" for n in names)
        self.record["target_classes"] = names
        return self.record["target_filter"]

    # -- category procedures ----------------------------------------------
    def screen(self):
        self.make_worktree()
        try:
            getattr(self, f"screen_{self.cat}")()
            self.record["status"] = "accepted"
        finally:
            self.drop_worktree()

    def screen_S(self):
        self.build("base", "base-build-failed")
        c = self.test("base-full-suite")
        if c["failed"]:
            raise Reject("base-suite-red")
        filt = self.set_filter(self.e["parent"])
        c = self.test("base-target", filt)
        if c["total"] == 0:
            raise Reject("filter-matches-no-tests")
        if c["failed"]:
            raise Reject("base-target-red")
        self.record["base_target_green"] = c
        self.apply_diff(self.e["prod_src_files"], "apply-prod-diff")
        self.build("stale", "stale-state-build-failure")
        c = self.test("stale-target", filt)
        if c["failed"] == 0:
            raise Reject("stale-state-green")
        self.record["stale_target_red"] = c
        self.record["stale_full_suite"] = self.test("stale-full-suite")

    def screen_P(self):
        self.build("base", "base-build-failed")
        c = self.test("base-full-suite")
        if c["failed"]:
            raise Reject("base-suite-red")
        filt = self.set_filter(self.e["sha"])
        self.apply_diff(self.e["test_src_files"] + self.e["spec_md_files"],
                        "apply-test-oracle-diff")
        self.build("oracle", "test-oracle-uncompilable")
        c = self.test("oracle-target", filt)
        if c["total"] == 0:
            raise Reject("filter-matches-no-tests")
        if c["failed"] == 0:
            raise Reject("test-oracle-green")
        self.record["oracle_target_red"] = c
        self.apply_diff(self.e["prod_src_files"], "apply-prod-diff")
        self.build("full", "full-state-build-failure")
        c = self.test("full-target", filt)
        if c["failed"]:
            raise Reject("full-state-target-red")
        self.record["full_target_green"] = c
        c = self.test("full-suite")
        if c["failed"]:
            raise Reject("full-state-suite-red")
        self.record["full_suite_green"] = c

    def screen_N(self):
        self.build("base", "base-build-failed")
        c = self.test("base-full-suite")
        if c["failed"]:
            raise Reject("base-suite-red")
        self.record["base_suite_green"] = c
        self.record["target_filter"] = None  # N target = full suite
        self.apply_diff(self.e["prod_src_files"], "apply-prod-diff")
        self.build("changed", "prod-change-breaks-build")
        c = self.test("changed-full-suite")
        if c["failed"]:
            raise Reject("suite-red-after-prod-change")
        self.record["changed_suite_green"] = c


def screen_entry(repo, exp_dir, entry, category):
    for attempt in (1, 2):
        s = Screener(repo, exp_dir, entry, category)
        s.record["attempt"] = attempt
        try:
            s.screen()
        except Reject as r:
            s.record["status"] = "rejected"
            s.record["reason"] = str(r)
        except Pipeline as p:
            s.record["status"] = "pipeline_error"
            s.record["reason"] = str(p)
        os.makedirs(s.case_dir, exist_ok=True)
        with open(os.path.join(s.case_dir, "record.json"), "w") as f:
            json.dump(s.record, f, indent=2)
            f.write("\n")
        if s.record["status"] != "pipeline_error" or attempt == 2:
            return s.record
        print(f"  {s.qid}: pipeline_error ({s.record['reason']}), retrying once")


def main():
    repo, exp_dir, category = sys.argv[1], sys.argv[2], sys.argv[3]
    queues = json.load(open(os.path.join(exp_dir, "screening_queues.json")))
    queue = queues["queues"][category]
    results = []
    accepted = 0
    for entry in queue:
        if accepted >= MAX_ACCEPT:
            results.append({"queue_id": entry["queue_id"], "sha": entry["sha"],
                            "status": "not-screened",
                            "reason": "quota-reached-before-position"})
            continue
        print(f"screening {entry['queue_id']} {entry['sha'][:8]} "
              f"{entry['subject'][:60]}", flush=True)
        rec = screen_entry(repo, exp_dir, entry, category)
        results.append({"queue_id": rec["queue_id"], "sha": rec["upstream_sha"],
                        "status": rec["status"], "reason": rec["reason"]})
        print(f"  -> {rec['status']}" +
              (f" ({rec['reason']})" if rec["reason"] else ""), flush=True)
        if rec["status"] == "accepted":
            accepted += 1
    out = {"category": category, "accepted": accepted, "results": results}
    metadata_path, metadata = load_metadata(exp_dir)
    metadata["selection"]["screening"][category] = out
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
        f.write("\n")
    print(f"category {category}: accepted {accepted}")


if __name__ == "__main__":
    main()
