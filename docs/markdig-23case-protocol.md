# Markdig 30-case experiment — pre-registered mining & screening protocol

Stage: candidate mining and empirical screening only. No model calls, no
mutation testing, no repair runs. Local commits only.

This protocol is frozen before any empirical screening run. Any deviation
found necessary during screening is recorded in `stage-log.md` with rationale;
the protocol text itself is not edited after the pre-registration commit.

## 1. Window and repository

- Repository: fork `Hamjoon/markdig` (upstream `xoofx/markdig`), local clone.
- Window: commits reachable from `fc705234fa211d179ee1d5e7656b51ab99f70ca9`
  ("Fix emoji table alignment regression (#943)") with commit date
  ≥ 2025-01-01, inclusive of the endpoint commit.
  Enumeration command: `git rev-list --no-merges --since=2025-01-01 fc705234…`.
  Independently verified counts: 137 commits total, of which 21 merges
  (excluded) and 116 non-merge commits enter classification.
- Base for every candidate: the candidate commit's first parent (recorded as
  `base_sha`). Parents may pre-date the window; that is allowed (the window
  constrains candidate commits, not their bases).

## 2. Path classification rules (frozen)

Applied to every path in a commit's diff (`git diff-tree -r --no-renames --numstat`):

| Class | Rule |
|---|---|
| `prod_src` | `src/Markdig/**/*.cs` |
| `prod_infra` | `src/Markdig/**` non-`.cs` (csproj, props, …) |
| `generated` | `src/Markdig.Tests/**/*.generated.cs` |
| `spec_md` | `src/Markdig.Tests/**/*.md` |
| `test_src` | `src/Markdig.Tests/**/*.cs` except `*.generated.cs` |
| `test_infra` | `src/Markdig.Tests/**` other files |
| `other` | everything else (Signed/Benchmarks/Fuzzing/WebApp/SpecFileGen/mdtoc/site/docs/CI/…) |

Markdown specs under `src/Markdig.Tests/**` are source files; `*.generated.cs`
is generated output (by `SpecFileGen` during build) and is never edited or
patched directly at any stage. Fixture states obtain generated-code changes
exclusively by applying the `.md` diff and rebuilding. Note: a few `.md` files
under `src/Markdig.Tests/` are plain test data with no `.generated.cs`
sibling; they are classified `spec_md` but contribute no test classes during
filter discovery (harmless).

"Test-side" below means `test_src` + `spec_md` (never `generated`,
never `test_infra`). "Production diff" below means `prod_src` paths only.

## 3. Exclusion rules (frozen; first matching reason wins; every exclusion recorded)

1. Merge commits (excluded by enumeration; counted).
2. `smoke-commit`: the three week-4 smoke commits
   `9dffce52b61068c4451399068f72cdad34f79bdb`,
   `50061841a45e142192362131c9ed2ea6043f302e`,
   `25506f20d96f214f951ac2d881550d8b883bf9f0`.
3. `no-production-source-change`: zero `prod_src` files changed. This single
   rule removes releases, dependency bumps, CI/docs/site changes,
   test-only commits, and generated-only or infra-only changes — none of them
   contain a production behavior change to screen.
4. `generated-without-spec-md`: commit touches `generated` files without
   touching any `spec_md` file (generated-file trap: desynced or hand-edited
   generated output).
5. `prod-diff-too-large`: more than **12** `prod_src` files or more than
   **600** changed `prod_src` lines (additions + deletions).
6. `test-diff-too-large`: more than **600** changed test-side lines
   (additions + deletions, `test_src` + `spec_md`).
   Rationale for 5–6: Markdig commits are small (median prod diff ≈ 30
   lines); these caps cut only the long tail (mass XML-doc commits, the
   2,100-line Unicode table commit) that cannot form controlled fixtures.
   Thresholds chosen from the window's numstat distribution **before** any
   screening run; frozen here.
7. `comment-only-prod-diff`: after stripping blank lines and lines starting
   with `//`, `///`, `/*`, `*`, `*/`, the production diff has zero changed
   lines (XML-doc/comment polish is not a production behavior change).
8. `patch-id-duplicate`: `git patch-id --stable` equal to an earlier
   (older) surviving commit — duplicate landings/cherry-picks; the first
   landing stays eligible.
9. `pr-repeat`: subject references an issue/PR number (`#\d+`) already
   referenced by an older surviving commit — repeated representations of the
   same PR/behavior; the first landing stays eligible.

Rules are evaluated oldest → newest so 8–9 deterministically keep first
landings.

## 4. Category heuristics (frozen; pools are disjoint)

Applied to surviving commits. Let `add`/`del` be test-side changed line
counts:

- **S pool** (expected future decision `fix_tests`): test-side `del > 0` —
  the commit rewrote existing test expectations, so its production change
  plausibly contradicts the old tests. (Week-4 lesson: additive-test commits
  are structurally non-viable for S; they are kept out of the S pool.)
- **P pool** (expected `fix_production`): test-side `add > 0` and `del == 0`
  — purely additive tests (regression-test-plus-fix commits).
- **N pool** (expected `no_change`): no test-side change at all — production
  change that upstream landed with no test edits.

Commits mis-assigned by the heuristic are handled by empirical screening
(rejected there), never re-assigned to another pool: an S-rejected commit is
not recycled into P or vice versa. This forgoes some yield in exchange for a
selection process with no adaptive branching.

## 5. Seed, shuffle, queues

- Seed: `20260731`.
- Each pool is listed in `git rev-list` order (newest → oldest), then
  shuffled with an independent PRNG per category:
  `random.Random("20260731:S" | "20260731:P" | "20260731:N")` (Python
  `random`, version-stable Mersenne Twister).
- Queue IDs `S-01…`, `P-01…`, `N-01…` in shuffled order. Queues are complete:
  every pool member appears exactly once; the full queues with metadata are
  committed before screening (`queues/queues.json`, `queues/mining-stats.json`
  produced by `scripts/mine.py`).
- Determinism acceptance test: two independent runs of `mine.py` must produce
  byte-identical outputs.

## 6. Screening procedure (frozen)

Screen each category strictly from the front of its queue. Accept the first
candidates that satisfy the executable conditions; stop at **10** accepted or
queue exhaustion. Never expand the window or relax rules to fill a shortfall;
report actual counts. Queue entries behind the stop point are recorded
`not-screened`. Order of categories: S, then P, then N (pools are disjoint, so
order cannot leak selections across categories).

### 6.1 Environment (pinned, recorded)

- macOS arm64 (this machine; exact `uname` in stage log), git ≥ 2.x.
- .NET SDKs installed user-locally at `~/.dotnet`: **10.0.302** and
  **9.0.316**. Per-candidate SDK/TFM rule: read `src/global.json` at the
  candidate's base; SDK major 10 → build/test `-f net10.0`; SDK major 9 →
  `-f net9.0`. The resolved `dotnet --version` is recorded per candidate.
- Environment for every dotnet command: `DOTNET_ROOT=$HOME/.dotnet`,
  `PATH=$HOME/.dotnet:…`, `DOTNET_CLI_TELEMETRY_OPTOUT=1`, `DOTNET_NOLOGO=1`,
  `DOTNET_CLI_UI_LANGUAGE=en` (forces parseable English runner output).
- Each candidate is screened in a fresh isolated worktree
  `.worktrees/screen-<queue-id>` at `base_sha`, removed afterwards. Worktrees
  and build products never enter the repository or the artifacts.

### 6.2 State construction

All states are built by applying path-restricted diffs of the candidate
commit onto its base worktree:
`git diff --no-renames <base> <sha> -- <paths> | git apply`.
The production diff uses `prod_src` paths only; the test-oracle diff uses
`test_src` + `spec_md` paths only. `*.generated.cs` is never in any apply
set (hard guard in the script); generated changes materialize only via
SpecFileGen rebuild from the patched `.md`.

### 6.3 Target filter discovery

- Candidate test classes are parsed from the changed test-side files
  (`class <Name>` declarations): for `test_src` files, from the file content
  at base (S) or at the candidate commit (P); for `spec_md` files, from the
  sibling `<name>.generated.cs` at the same revision.
- Target filter: `FullyQualifiedName~<Class>` terms OR-ed with `|`
  (class-level, robust to test renames within the commit — week-4 lesson).
- The filter is then executed with `dotnet test --filter` and the actual
  red/green counts and failing test names are read from runner output; a
  filter matching zero tests rejects the candidate
  (`filter-matches-no-tests`).
- N candidates have no test-side files; their target is the full
  `Markdig.Tests` suite for the pinned TFM.

### 6.4 Executable acceptance conditions

Common to all: every build must succeed; every test count is parsed from the
English runner summary (`Failed: X, Passed: Y, Skipped: Z, Total: T`);
"green" = `failed == 0`, "red" = `failed > 0`. Build failure in a constructed
state is a **selection rejection** (reasons below), not a pipeline error —
red must mean failing tests, not a broken compile.

**S** — stale-test fixture, future expected decision `fix_tests`:
1. Build at base OK; full suite green (`base-suite-red` otherwise).
2. Target filter (base-rev classes) green and non-empty at base
   (`base-target-red`, `filter-matches-no-tests`).
3. Apply production diff; build OK (`stale-state-build-failure`);
   same target filter **red** (`stale-state-green` otherwise — the week-4
   smoke-3 failure mode).
4. Record stale-state full-suite counts (blast radius, informational).

**P** — missing-production-fix fixture, future expected `fix_production`:
1. Build at base OK; full suite green.
2. Apply test-oracle diff; build OK (`test-oracle-uncompilable` — expected
   common C# failure mode when new tests reference new APIs);
   target filter (commit-rev classes) **red** and non-empty
   (`test-oracle-green`, `filter-matches-no-tests`).
3. Apply production diff; build OK (`full-state-build-failure`); same target
   filter **green** (`full-state-target-red`); full suite green
   (`full-state-suite-red`).

**N** — no-change fixture, future expected `no_change`:
1. Build at base OK; full suite green.
2. Apply production diff; build OK (`prod-change-breaks-build`); full suite
   **green** (`suite-red-after-prod-change`).

### 6.5 Failure taxonomy, retries

- **Selection rejection** (`status=rejected`): the candidate fails an
  executable condition above. Recorded with reason; screening moves to the
  next queue entry.
- **Pipeline error** (`status=pipeline_error`): tool/environment fault
  (worktree/apply/diff machinery, unparseable runner output, timeout).
  Retried once from scratch; if it persists, recorded and the queue moves on
  without counting the candidate as rejected-by-selection.
- Timeouts: 900 s per build, 900 s per test run.

### 6.6 Recorded evidence (per screened candidate)

`screening/<queue-id>/record.json`: base/upstream SHA, subject, category,
changed production/test paths, construction steps with commands, discovered
filter and classes, every run (command, rc, red/green counts, failing test
names), build results, SDK/TFM, status and acceptance/rejection reason,
attempt number. `screening/<queue-id>/logs/`: sanitized command output
(worktree, repo, and home paths replaced by placeholders; failures keep more
tail than successes). No build products, no credentials, no absolute local
paths, no personal identifiers (explicit week-4 regression: a coverage
artifact leaked a hostname; nothing machine-identifying is stored this time).

## 7. Acceptance manifest and caps

Up to 10 accepted per category, in queue order. Each accepted case gets a
case ID equal to its queue ID. `cases.json` is generated from the
records; every accepted SHA must be unique, absent from the smoke set, and
appear in exactly one category.

## 8. Deliverables

1. This protocol (pre-registered).
2. `queues/queues.json`, `queues/mining-stats.json` (complete seeded queues,
   pool stats, every exclusion with reason).
3. `scripts/mine.py`, `scripts/screen.py` (rerunnable).
4. `cases.json` manifest.
5. `screening-report.md` (pools, ordered results, evidence, counts,
   limitations, shortfalls).
6. `verification-report.md` (executable red/green/build evidence).
7. `stage-log.md` (chronological; environment, deviations, retries,
   pre-registration and completion commit SHAs).

## 9. Known limitations (pre-registered)

- Strict "red = failing tests, compiling state" thins the S pool
  (obsolete-API removals) and the P pool (new-API tests) — reported as
  rejections, not worked around.
- Class-level filters may include unrelated tests in the same classes; the
  executable conditions still hold (base/full-state green requirements bound
  the noise).
- The S heuristic keys on test-side deletions; a commit that changed
  behavior *and* only added tests is invisible to S (routed to P). No
  recycling between pools.
- The N full-suite condition cannot prove behavior preservation beyond the
  suite's coverage; N cases are "suite-green", not "semantically identical".
- Single machine, single OS/architecture; results are environment-pinned,
  not portable claims.
