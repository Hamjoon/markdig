# Markdig 30-case experiment — stage log (mining & screening)

Chronological log. All times local, 2026-07-31.

## Environment

- Machine: macOS Darwin 25.3.0 arm64 (different machine from the week-4 smoke
  run, which was Darwin 25.5.0; no hostname/user identifiers recorded).
- git 2.x local clone of fork `Hamjoon/markdig`; branch
  `experiment/2026-07-week5-markdig-30case` at `fc705234`.
- .NET: no SDK present at session start. Installed user-locally via the
  official `dotnet-install.sh` into `~/.dotnet`: SDK **10.0.302** (same
  version as the week-4 smoke run) and SDK **9.0.316** (required because
  every commit before `e5c88eff` 2026-02-21 pins `global.json` to 9.0.100
  with `rollForward: latestMinor`, which never rolls to SDK 10).
- Env for all dotnet commands: `DOTNET_ROOT=$HOME/.dotnet`,
  `PATH=$HOME/.dotnet:…`, `DOTNET_CLI_TELEMETRY_OPTOUT=1`, `DOTNET_NOLOGO=1`,
  `DOTNET_CLI_UI_LANGUAGE=en`.

## 2026-07-31 — independent review (before protocol freeze)

- Reviewed week-4 branch `experiment/2026-07-week4-markdig-smoke`
  (scaffold `57193a3a`, fixtures `e5c7f3ca`, artifacts `caf61951`),
  `batch-log.md`, `cases.json`, scripts. Key carried-over lessons:
  (1) additive-test commits are structurally non-viable for S (smoke-3);
  (2) class-level filters, discovered from runner output, survive test
  renames; (3) `DOTNET_CLI_UI_LANGUAGE=en` is required for parseable output;
  (4) first build in a fresh worktree regenerates all `*.generated.cs`
  byte-stably; (5) a smoke coverage artifact leaked a hostname-bearing
  filename — this stage stores no coverage output and sanitizes paths.
- Window verified independently: 137 commits since 2025-01-01 through
  `fc705234` (21 merges + 116 non-merge) — matches the preliminary scan.
- Repo was a blob-less partial clone (`partialclonefilter=blob:none`) with
  two objects unfetchable on demand; screening in worktrees would have hit
  network faults. **Deviation/fix (pre-registration):** ran
  `git fetch --refetch --no-filter origin main`, unset the filter, set
  `remote.origin.promisor=false`; object db now complete (verified by
  enumerating all window objects).
- Multi-target audit: TFMs move `net6.0;net8.0;net9.0` →
  `net8.0;net9.0` → `net8.0;net10.0` across the window; SDK pin moves
  9.0.100 → 10.0.100 at `e5c88eff`. Frozen rule: pick TFM by `global.json`
  major at the candidate's base (net9.0 vs net10.0), record resolved SDK.
- Toolchain pilots (environment validation only, no candidate screened;
  old-era pilot deliberately at `5b323913`, a deps-only commit that is
  never pool-eligible):
  - `fc705234` + SDK 10.0.302 `-f net10.0`: build OK, suite
    `Failed: 0, Passed: 3795, Skipped: 1, Total: 3796` (~1 s).
  - `5b323913` (2025-01-10) + SDK 9.0.316 `-f net9.0`: build OK, suite
    `Failed: 0, Passed: 3447, Skipped: 1, Total: 3448`.
- Classifier findings folded into the protocol before freezing: `.csproj`
  changes must not count as prod/test source (they polluted a first-pass
  numstat scan, e.g. the net10 bump landed in an S pool draft); `.md` files
  without `.generated.cs` siblings are data, not specs; commit `09a4b81a`
  ("Update tests") edits a generated file with no `.md` change — motivates
  the `generated-without-spec-md` exclusion.

## 2026-07-31 — mining (pre-registration)

- `scripts/mine.py` run on the frozen window, seed `20260731`:
  116 non-merge commits → 49 excluded (3 smoke-commit,
  42 no-production-source-change, 2 prod-diff-too-large,
  2 comment-only-prod-diff) → pools S=12, P=23, N=32.
- Determinism proven: second run to a scratch directory is byte-identical
  (`diff` clean) ; canonical sha256 of queues.json:
  `0578d21953459aa81684a5470c59d15a0574c712d0066812bfa91d70251a0c4d`.
- Pre-registration commit (protocol, mine.py, screen.py, queues, this log up
  to this line): SHA recorded below after committing.

- **Pre-registration commit: `4c2a0fdab1d8ec95d6f7270b4bf49c8002aac92f`**
  (the placeholder in that commit's copy of this log is resolved here; the
  protocol/scripts/queues content is byte-identical to the pre-registered
  copy).

## 2026-07-31 — S screening (candidate mining stage, S category only)

- Environment reused from above; `uname -srm` = `Darwin 25.3.0 arm64`.
  SDKs present at `~/.dotnet`: 10.0.302 and 9.0.316. TFM/SDK selected
  per-candidate from `src/global.json` at the base (net10.0 → 10.0.302,
  net9.0 → 9.0.316), recorded in each `record.json`.
- **Interrupted-run recovery (deviation, mechanical only — no protocol,
  queue, or selection-logic change):** a prior S run had completed S-01…S-08
  (terminal records intact) and died mid-S-09, leaving the worktree
  `.worktrees/screen-S-09` (detached at S-09's base) and an incomplete
  `screening/S-09/` holding only `logs/` (no `record.json`). Removed exactly
  those two incomplete artifacts (`git worktree remove --force` + `rm -rf
  screening/S-09`); S-01…S-08 records/logs were left untouched. Screening then
  resumed from S-09 in strict seeded queue order via the frozen
  `screen.screen_entry`, reusing the already-terminal S-01…S-08 records
  (their logs carry non-deterministic build/test durations, so re-running the
  deterministic head would have needlessly rewritten preserved artifacts). The
  resume driver replicates `screen.main()`'s selection loop verbatim
  (front-to-back walk, `MAX_ACCEPT=10` gating, `not-screened` marking) and
  wrote `screening/S-results.json` in `main()`'s exact format. The driver is a
  scratch harness (kept in `/tmp`, not committed); no frozen file was edited.
- **Retries/pipeline errors:** none. Every screened candidate reached a
  terminal selection verdict on attempt 1; 0 pipeline errors, 0 retries.
- **Outcome — S queue exhausted (all 12 screened; < 10 accepted, so no
  `not-screened` entries):** accepted 3, rejected 9, pipeline_error 0,
  not-screened 0.
  - Accepted (case ID = queue ID):
    - S-05 `12590e5fbe1730984e0783452666a67df8e0b806` (base
      `8c01cf054971a1ec4cd663edaca6e2d035236133`) — "feat(link-helper):
      improve ASCII normalization handling (#911)"; net9.0 / 9.0.316; base
      target 90 green, stale target 7 failed.
    - S-07 `5365879a23c9f680b9ca6926783daa3f73795dc5` (base
      `a9bd7c6a5e1a0bd0992555ce3aeeafb4d4aee438`) — "Fix AbbreviationExtension
      corrupting emphasis/bold/italic resolution (#935) (#936)"; net10.0 /
      10.0.302; base target 74 green, stale target 1 failed.
    - S-09 `148fd08b1d5604177637307d82e6b83079642d63` (base
      `c488a27497199aa520df540ffecf1e159fbc06a1`) — "Add span
      validation/update APIs and tests"; net10.0 / 10.0.302; base target 65
      green, stale target 2 failed (TestDefinitionList, TestDefinitionList2).
  - Rejection taxonomy (9): `stale-state-green` ×7 (S-01, S-02, S-06, S-08,
    S-10, S-11, S-12 — production diff applied but the base-rev target filter
    stayed green: the commit's behavior change is not contradicted by the old
    tests under a class-level filter), `base-suite-red` ×1 (S-03 — base full
    suite not green at that base), `stale-state-build-failure` ×1 (S-04 —
    production-only diff does not compile against base test sources; a
    selection rejection, not a pipeline error).
- **Validation performed (all clean):** every S JSON artifact parses;
  `screening/S-results.json` agrees with all 12 per-case records (status,
  reason, sha, and queue order) and its accepted count (3) matches; each
  accepted record satisfies the S executable condition (base-target
  failed==0 & total>0, stale-target failed>0); leak scan over
  `screening/**` found no `/Users/…`, home dir, username, hostname, git
  author name/email, or project-path (`.openclaw`) strings; 54 log files
  carry the `<worktree>`/`<repo>`/`<home>` placeholders. No worktrees remain
  (`git worktree list` shows only the main checkout).
- P and N screening intentionally not started in this turn.
- **S screening completion commit:
  `801c23551686e06ec5b765f15399cd5201464c85`** (this SHA was the placeholder
  in that commit's copy of this log; resolved here in the P screening commit).

## 2026-07-31 — P screening (candidate mining stage, P category only)

- Environment reused verbatim from above; `uname -srm` = `Darwin 25.3.0
  arm64`. SDKs at `~/.dotnet`: 10.0.302 and 9.0.316. TFM/SDK selected
  per-candidate from `src/global.json` at the base (net10.0 → 10.0.302,
  net9.0 → 9.0.316), recorded in each `record.json`.
- **Interrupted-run recovery (deviation, mechanical only — no protocol,
  queue, or selection-logic change):** a prior P run had completed P-01…P-03
  (terminal `rejected` records intact) and died mid-P-04, leaving the worktree
  `.worktrees/screen-P-04` (detached at P-04's base) and an incomplete
  `screening/P-04/` holding only `logs/01-build-base.txt` (no `record.json`).
  Removed exactly those two incomplete artifacts (`git worktree remove
  --force` + `rm -rf screening/P-04`); P-01…P-03 records/logs left untouched.
  Screening then resumed from P-04 in strict seeded queue order via the frozen
  `screen.screen_entry`, reusing the already-terminal P-01…P-03 records (their
  logs carry non-deterministic build/test durations, so re-running the
  deterministic head would have needlessly rewritten preserved artifacts). The
  resume driver replicates `screen.main()`'s selection loop verbatim
  (front-to-back walk, `MAX_ACCEPT=10` gating, `not-screened` marking) and
  wrote `screening/P-results.json` in `main()`'s exact format. The driver is a
  scratch harness (kept in `/tmp`, not committed); no frozen file was edited.
- **Retries/pipeline errors:** none. Every screened candidate reached a
  terminal selection verdict on attempt 1; 0 pipeline errors, 0 retries.
- **Outcome — quota reached at P-17 (10 accepted); P-18…P-23 recorded
  `not-screened`:** of 23 P entries, 17 screened (P-01…P-17), 6 not-screened.
  accepted 10, rejected 7, pipeline_error 0, not-screened 6.
  - Accepted (case ID = queue ID); "oracle-red" = target filter failed/total
    after the test-oracle diff, "full-green" = same filter after the
    production diff:
    - P-04 `d548b82bcd269c34221d06a007b06f3ea33ed236` (base
      `7ff8db901659`) — "Add support for a table without an extra new line
      before it"; net9.0 / 9.0.316; oracle-red 2/15, full-green 0/15.
    - P-06 `781d9b536598e0b770c1eabbe58d2ac76b285409` (base
      `543570224e94`) — "Remove leading newline in block attributes (#896)";
      net9.0 / 9.0.316; oracle-red 1/4, full-green 0/4. (spec_md+generated
      candidate: spec diff applied, `.generated.cs` regenerated by build.)
    - P-07 `fcbf8170633e7e1025a37718af9c253698166b52` (base
      `5dca4149a518`) — "Fix CJK emphasis after HTML entity newlines (#941)";
      net10.0 / 10.0.302; oracle-red 3/107, full-green 0/107.
    - P-08 `5a3c206076621dd75c6f0ec36236f031ebbadea2` (base
      `682c727288de`) — "Fixes #878: render indent and 0 blocks"; net9.0 /
      9.0.316; oracle-red 1/125, full-green 0/125.
    - P-09 `800235ba7ab773ac3ea691d16e4bb17a1f9b0200` (base
      `d5f8a809a00d`) — "Fix IndexOutOfRangeException in CodeInlineParser
      (#900)"; net9.0 / 9.0.316; oracle-red 1/46, full-green 0/46.
    - P-11 `0f98267a8519ee6563dceae5ee31db3d60d2844f` (base
      `fcbf8170633e`) — "Fix pipe table cells with unmatched subscript
      (#932)"; net10.0 / 10.0.302; oracle-red 1/23, full-green 0/23.
    - P-14 `b15cf582a538e0c0e016e70cb8a0f03d4f2d55d8` (base
      `61e9be290b1d`) — "Add 'search' HTML tag support"; net9.0 / 9.0.316;
      oracle-red 1/62, full-green 0/62.
    - P-15 `b83641351f67e2c2f240167f9314aeb354714dad` (base
      `0f98267a8519`) — "Fix roundtrip autolink URLs (#919)"; net10.0 /
      10.0.302; oracle-red 3/12, full-green 0/12.
    - P-16 `d6e88f16f7d2d86a096a552250f89415513d09dc` (base
      `03bdf6008631`) — "Fix pipe table parsing with a leading paragraph
      (#905)"; net9.0 / 9.0.316; oracle-red 2/60, full-green 0/60.
      (spec_md+generated candidate: 2 spec_md diffs applied, 2
      `.generated.cs` regenerated by build.)
    - P-17 `bc4e399087e19ddbbdf95dc698bec7f752b3c8e5` (base
      `9dffce52b610`) — "Fix blockquote ordered list parsing (#887)";
      net10.0 / 10.0.302; oracle-red 1/51, full-green 0/51. (Base is a
      week-4 smoke commit; the smoke-commit exclusion applies to candidate
      SHAs, not bases — protocol §1/§3 — so this candidate is eligible.)
  - Rejection taxonomy (7): `test-oracle-uncompilable` ×6 (P-01, P-02, P-03,
    P-10, P-12, P-13 — the additive-test diff references new production APIs
    that do not exist at base, so the oracle state does not compile; the
    expected common C# failure mode named in protocol §6.4), `test-oracle-green`
    ×1 (P-05 — after the test-oracle diff the target filter was already green,
    so the new tests do not actually exercise a missing production fix).
  - Not-screened (6): P-18…P-23, `quota-reached-before-position` (10 accepted
    reached at P-17; per protocol §6 the window is never expanded to fill).
- **Validation performed (all clean):** every P JSON artifact parses;
  `screening/P-results.json` agrees with all 17 per-case records (status,
  reason, sha, and queue order) and its accepted count (10) matches; each
  accepted record satisfies the P executable condition (base build OK &
  base full suite failed==0; oracle-target failed>0 & total>0; full-target
  failed==0; full suite failed==0; all three builds rc0); all 10 accepted
  SHAs are unique, absent from the smoke set, and appear only in P; no
  `.generated.cs` path entered any apply set (hard guard held). Leak scan
  over `screening/**` found no absolute path, home dir, username, hostname,
  git author name/email, or project-path (`.openclaw`) strings; the only
  P logs without `<worktree>`/`<repo>`/`<home>` placeholders are terse
  "Build succeeded" outputs that contain no paths at all. P-18…P-23 created
  no directories. No worktrees remain (`git worktree list` shows only the
  main checkout).
- N screening intentionally not started in this turn.
- **P screening completion commit:
  `8e414c60571bbc99da4ac103876c20a41c2bb72f`** (this SHA was the placeholder
  in that commit's copy of this log; resolved here in the N screening commit).

## 2026-07-31 — N screening (candidate mining stage, N category only)

- Environment reused verbatim from above; `uname -srm` = `Darwin 25.3.0
  arm64`. SDKs at `~/.dotnet`: 10.0.302 and 9.0.316. TFM selected
  per-candidate from `src/global.json` major at the base (major 10 → net10.0,
  major 9 → net9.0); resolved `dotnet --version` recorded per candidate.
- **No interruption/recovery:** unlike the S and P stages, the N run started
  from a clean state — no prior N worktree, no partial `screening/N-*`
  artifacts, `.worktrees/` empty. Screening was therefore driven directly by
  the frozen `screen.main()` (`python3 scripts/screen.py <repo> <exp-dir> N`),
  which walks the N queue front-to-back with `MAX_ACCEPT=10` and writes
  `screening/N-results.json` in its own format; no resume/scratch driver was
  used and no frozen file was edited.
- **Retries/pipeline errors:** none. Every screened candidate reached a
  terminal selection verdict on attempt 1; 0 pipeline errors, 0 retries.
- **SDK roll-forward observation (frozen behavior, not a deviation):** two
  accepted bases (N-06 `88c5b5cb410f`, N-09 `d1233ffe66da`) pin
  `global.json` to `9.0.100` with `rollForward: latestMajor`. The frozen
  per-candidate rule reads the global.json major (9 → `-f net9.0`) while
  `dotnet --version` rolls forward across majors to the only installed 10.x
  SDK, so those two records show `net9.0` built under SDK `10.0.302`. Both
  built clean and kept the full suite green; this is the expected output of
  the frozen rule (TFM from global.json major; record the resolved SDK), not
  a change to protocol, queue, or selection logic. The other eight bases
  resolve the clean split (net9.0 → 9.0.316 for `latestMinor` 9.x pins,
  net10.0 → 10.0.302 for 10.x pins).
- **Outcome — quota reached at N-10 (10 accepted); N-11…N-32 recorded
  `not-screened`:** of 32 N entries, 10 screened (N-01…N-10), 22
  not-screened. accepted 10, rejected 0, pipeline_error 0, not-screened 22.
  Every one of the first ten queue positions accepted (the N executable
  condition — base build OK, base full suite green, production-only diff
  applied, changed build OK, changed full suite green — held for each), so
  the quota was reached without reaching any rejection. "suite" below is the
  full `Markdig.Tests` suite count (base == changed for every accepted case;
  N's target is the full suite, `target_filter` = null):
  - N-01 `adfcf42529649e1e4bf5e95e152411577e9f7eec` (base `dab1ca548373`) —
    "Use FrozenDictionary in a couple places"; net9.0 / 9.0.316; suite
    Passed 3453, Skipped 1, Total 3454, Failed 0 before and after.
  - N-02 `8269ff1af54456c97e58b53c5f6d3f4eaa24875b` (base `0e6d0f4cb24c`) —
    "Improve AutoLinkParser overhead for false-positive opening chars";
    net9.0 / 9.0.316; suite 3468/1/3469.
  - N-03 `ec2eef25b2a70dfab54e2636f50d14f2a0b8ca08` (base `6261660d377e`) —
    "Remove HtmlHelper.UnescapeNullable"; net9.0 / 9.0.316; suite
    3539/1/3540.
  - N-04 `aab5543cb5b3bd78cf5222144e411f0f52672504` (base `2e1d741aaf15`) —
    "Code cleanup"; net9.0 / 9.0.316; suite 3541/1/3542.
  - N-05 `14406bc60d515bfe3bc96b017560d22fb5b9805b` (base `2aa6780a3071`) —
    "Fixes issue #845"; net9.0 / 9.0.316; suite 3543/1/3544.
  - N-06 `148278417f5aeee2e523ee9ad2fea4500320fa23` (base `88c5b5cb410f`) —
    "Added error throwing when stack is empty and PopIndent() is called";
    net9.0 / 10.0.302 (latestMajor roll-forward, above); suite 3444/1/3445.
  - N-07 `c488a27497199aa520df540ffecf1e159fbc06a1` (base `58e8217ddb0d`) —
    "Document parser authoring contracts and migration risks"; net10.0 /
    10.0.302; suite 3606/1/3607. (This candidate SHA is also the recorded
    base of accepted S-09; base/candidate overlap across pools is allowed —
    protocol §1 constrains candidate SHAs, and the pools remain disjoint by
    candidate SHA.)
  - N-08 `90c73b775453734fbfb28cde78c19b5c9f6139e9` (base `ee403ce28f1a`) —
    "Update src/Markdig/Helpers/LinkHelper.cs"; net9.0 / 9.0.316; suite
    3453/1/3454.
  - N-09 `3e0c72f0430cb58d7aa9caf325bd780325229e17` (base `d1233ffe66da`) —
    "Fixes exception in DefinitionListParser.GetCurrentDefinition"; net9.0 /
    10.0.302 (latestMajor roll-forward, above); suite 3444/1/3445.
  - N-10 `6261660d377e28430c0b01a0efc1f55476f86a45` (base `6d1fa96389c8`) —
    "Explain why not to normalize link title into empty strings"; net9.0 /
    9.0.316; suite 3539/1/3540.
  - Rejection taxonomy: none (0 rejections; the first ten queue entries all
    satisfied the N executable condition).
  - Not-screened (22): N-11…N-32, `quota-reached-before-position` (10
    accepted reached at N-10; per protocol §6 the window is never expanded to
    fill, and screening stops at the quota). These entries created no
    directories.
- **Validation performed (all clean):** every N JSON artifact parses;
  `screening/N-results.json` agrees with all 10 per-case records (status,
  reason, sha, and queue order) and its accepted count (10) matches; the
  results `results` array is in exact N queue order for all 32 positions and
  every row's sha matches the queue sha; each accepted record satisfies the N
  executable condition (base build rc0 & base full suite failed==0 &
  total>0; changed build rc0 & changed full suite failed==0 & total>0) and
  carries `target_filter` = null; every accepted case's construction applied
  `prod_src` paths only with no `.generated.cs` in any apply set (hard guard
  held); all 10 accepted SHAs are unique, absent from the smoke set, disjoint
  from the accepted S and P SHAs, and appear only in the N pool. Leak scan
  over `screening/N-*/**` found no absolute path, home dir, username,
  hostname, git author name/email, or project-path (`.openclaw`) strings; log
  files carry the `<worktree>`/`<repo>`/`<home>` placeholders (or contain no
  paths at all). N-11…N-32 created no directories. No worktrees remain
  (`git worktree list` shows only the main checkout).
- Later stages (manifest generation, main experiment, reporting)
  intentionally not started in this turn.
- **N screening completion commit:
  `771692a0b53d411661a3a8729ce630c9635214a8`.**

## 2026-07-31 — 23-fixture freeze and fresh verification

- The pre-registered screening outcome was retained without expansion or
  relaxation: **S=3, P=10, N=10 (23 total)**. S exhausted its complete
  12-entry queue at three accepted cases; this shortfall remains an observed
  selection result.
- Reviewed and strengthened the previously untracked freeze helpers before
  use. `scripts/manifest.py` now validates complete queue/result ordering,
  record identity, all required build and test conditions, non-empty test
  targets, category counts, construction paths, generated-file guards,
  candidate-SHA uniqueness, and smoke-candidate exclusion. It writes the
  manifest only after every invariant passes. `scripts/verify.py` refuses to
  mix with an existing verification directory and compares both exact test
  counts and fixture identity against the original screening records.
- Generated `accepted-cases.json`: schema 1, protocol commit `4c2a0fda`,
  completed screening artifact commit `771692a0`, counts S=3/P=10/N=10,
  23 unique cases. Manifest SHA-256:
  `2e2a4425d8ccf356ed843a806ddf335837e6cf87d42c7e4d7f20be3903a02552`.
- Fresh verification command:
  `python3 -u experiments/markdig-30case/scripts/verify.py .
  experiments/markdig-30case`. It reconstructed all 23 fixtures in new
  `.worktrees/verify-<case-id>` worktrees, rebuilt them, and reran the frozen
  executable procedure. **All 23 accepted again; 23/23 exact test-count
  matches; 23/23 exact fixture-identity matches; 0 rejections; 0 pipeline
  errors.** Verification produced 23 records and 128 sanitized command logs,
  then removed every temporary worktree.
- Generated `verification-results.json` with `all_ok=true`; SHA-256:
  `b0b8711991acf08dc70b667f16cd9ae45d6491dcaaa07e5ea5abe4fe00a64703`.
- Wrote the English `screening-report.md` and `verification-report.md`.
  The former records the S shortfall and complete 23-case manifest; the
  latter records per-case fresh red/green evidence and the integrity audit.
- Final pre-commit audit: all JSON parsed; category result rows, records, and
  queue SHAs agreed; accepted SHAs were unique and outside the smoke set; no
  generated C# file entered an apply set; leak scans found no local absolute
  path, username, hostname, or workspace identifier; `git worktree list`
  showed only the main checkout.
- No model-under-test run, repair run, or post-freeze experiment stage was
  started. Work stops at this gate after the local fixture-freeze commit.
- **Fixture-freeze commit: the commit containing this section; exact SHA is
  reported in the stage handoff.**

## 2026-07-31 — GPT-OSS raw model-run gate

- Froze the English single-turn prompt template, 23 case-specific prompts,
  execution script, and input digests before contacting the model. The
  pre-run protocol/input commit is
  `0ccd9e909db7aa5b726f3bbc5d113825e6822eb1`.
- Executed exactly one primary OpenRouter chat-completions trial for each of
  the 23 frozen fixtures, in manifest order, with
  `openai/gpt-oss-120b`, temperature 0, and no assistant history.
- **23/23 assistant responses received.** The API returned
  `openai/gpt-oss-120b` for all 23 calls and `finish_reason=stop` for all 23.
  Every response arrived on attempt 1: 23 primary trials, 0 transport
  retries, 0 no-response records, and 0 error files.
- Raw evidence stored per case: `gptoss-response.md`, `gptoss-usage.json`,
  and `gptoss-run.json`. Aggregate usage was 75,626 prompt tokens, 34,534
  completion tokens, and 110,160 total tokens; the API-reported aggregate
  cost was USD 0.011487683.
- Structural audit passed: 23 response files, 23 usage files, and 23 run
  metadata files; every prompt digest matched the frozen input, every
  response digest matched its stored response, and the raw-artifact scan
  found no credential, local absolute path, username, hostname, or workspace
  marker.
- The first-line output contract was structurally satisfied in all 23 raw
  responses (16 `fix_production`, 7 `no_change`). These counts are recorded
  only as response-shape evidence; no expected-label comparison, patch
  application, repair test, or outcome scoring was performed at this gate.
- Patch application, repair validation, signal analysis, and final report
  audit were intentionally not started. Mutation testing remains excluded by
  instruction. Work stops at this gate pending explicit approval.
- **Raw model-run artifact commit: the commit containing this section; exact
  SHA is reported in the stage handoff.**

## 2026-07-31 — repair, signal, and report audit

- Froze the repair/signal rules and evaluator before canonical execution.
  Initial protocol commit: `84b095f701a3904a85cbfe8416c74b91cfb52b11`.
- A pre-canonical local pass exposed an evaluator implementation defect: the
  parser accepted paired file headers followed by bare `@@` markers as
  format-valid and deferred rejection to `git apply`. The written protocol
  already required an ordinary unified diff. No raw model response was
  changed or rerun. The generated pre-pass evaluation directory/results were
  discarded, numeric hunk-header validation was added in
  `7d6b9ce85feb9a581a3bfd60dab9a0579b01a714`, and canonical evaluation was
  rerun from scratch.
- Canonical exact-decision result: **17/23 (73.9%)** — S 0/3, P 10/10,
  N 7/10. Confusion counts: expected `fix_tests` → `fix_production` 3;
  expected `fix_production` → `fix_production` 10; expected `no_change` →
  `no_change` 7 and `fix_production` 3. The model never chose `fix_tests`.
- Full response-contract validity: **7/23 (30.4%)**. All first-line decision
  tokens were valid, but all 16 fix responses used malformed unified diffs
  with bare `@@` hunk markers; five also lacked paired file headers. No path
  or hunk metadata was inferred, and no malformed model patch was applied.
- Strict signal result: **7/23 (30.4%)** — S 0/3, P 0/10, N 7/10. The seven
  correct N no-change cases rebuilt and reran a green full suite with exact
  count matches to fixture verification. Pipeline errors 0; infrastructure
  retries 0; all canonical cases completed on attempt 1.
- Wrote `evaluation-results.json`, 23 per-case canonical records, extracted
  patch evidence for the 16 fix responses, 21 sanitized command logs,
  `evaluation-report.md`, and the integrated English `final-report.md`.
- Integrity checks reconciled aggregate and per-case flags, raw response
  SHA-256 values, decision matrix, full-suite counts, category order, and
  failure taxonomy. Leak scan found no credential, local path, username,
  hostname, or workspace marker; no temporary worktrees remain.
- Mutation testing remained excluded by instruction; no Stryker command or
  mutation-derived result was produced.
- **Evaluation/report artifact commit: the commit containing this section;
  exact SHA is reported in the final handoff.**

## 2026-07-31 — Zod-equivalent evaluation correction

- The preceding 0/16 application result is superseded. It stopped on model
  diff formatting before application, whereas Zod Week 4 used a four-stage
  cascade ending in a context-matching applier. The earlier result was
  therefore not methodologically comparable with Zod.
- No model response was changed or regenerated. The same 23 raw GPT-OSS
  responses from commit `f9e96fd7d78c49433f303bdc46cea517c1c61b45`
  were reevaluated.
- Froze the corrected protocol and evaluator in
  `d40a391b498214c28c37b6092f1d77ec6a715344`. The implementation is pinned to
  Zod Week 4 commit `53aaeb99d50a253d83f5dc18791b118c480ea8db`
  and records the source SHA-256 values for `apply-patch.py` and `validate.sh`.
- Tried every fix response in the fixed order: ordinary `git apply`,
  `git apply --recount`, `patch` with fuzz 3, then Zod-style context matching,
  resetting to an identical committed fixture before each method.
- Corrected application result: **13/16 applied (81.3%)**, all by context
  matching. S-05, P-08, and P-14 did not apply. All 13 normalized repair diffs
  changed only frozen allowed paths on the decision-named side; no generated
  C# path was touched.
- Required repair result: **2/13 (15.4%)**. P-06 and P-09 applied, preserved
  the fixture change, built, and passed both the non-empty target and full
  suite. Five other applied P patches left test failures; P-17 failed to build.
  The two applied S patches failed to build and failed preservation.
- All three N false-positive fixes applied and left the full suite green, but
  each failed `git apply --reverse --check fixture.patch`, proving that it
  removed or altered the intended recent production change. The seven correct
  N no-change cases remained green and preserved.
- Corrected exact decision remains **17/23 (73.9%)**. Corrected strict signal is
  **9/23 (39.1%)** — S 0/3, P 2/10, N 7/10. Pipeline errors 0;
  infrastructure retries 0.
- Replaced the evaluation JSON, per-case records/logs, evaluation report, and
  integrated English report. Mutation testing remained excluded; no Stryker
  command or mutation-derived judgment was produced.
- After the completed local audit, Gary explicitly approved publication to a
  personal fork for easier review. Created `agent-eli/markdig` as a fork of
  `xoofx/markdig` and published branch
  `experiment/2026-07-week5-markdig-30case-archive` as a parentless artifact
  branch containing only the experiment bundle. No upstream PR was opened.

## 2026-07-31 — Archive layout normalization

- Reorganized the public orphan branch to match the Zod Week 4 archive shape:
  `.gitignore`, `README.md`, `docs/`, `experiments/test-maintenance/`, and
  root `scripts/`.
- Consolidated each accepted fixture, immutable model exchange, repair
  evidence, result, and final validation output into one
  `cases/<case>-<sha8>/` packet without rerunning or changing any model output.
- Moved all reports, protocols, and this stage log into `docs/`.
- Kept exactly three root entry points for candidate mining, GPT-OSS execution,
  and Markdig signal evaluation. Mutation tooling remains excluded.
- The full-history branch retains the raw candidate-screening and fresh
  verification command logs intentionally omitted from the compact public
  archive.

## 2026-08-01 — Public metadata compaction

- Reduced the experiment root to the same three canonical JSON artifacts used
  by the Zod Week 4 archive: `cases.json`, `results-summary.json`, and
  `screening_queues.json`.
- Consolidated the non-derivable mining, screening, and fresh fixture-
  verification records into `metadata/experiment.json`.
- Removed aggregate model-input, model-run, and audit JSON files that can be
  reconstructed from the 23 case packets and reports. No fixture, prompt,
  model response, result, repair evidence, or validation log changed.
- Updated the pipeline helpers to read per-case input/run records and the
  consolidated metadata rather than recreating the removed root JSON files.

## 2026-08-01 — Supplemental coverage protocol freeze

- Confirmed that the original Markdig run had no Coverlet, XPlat Code
  Coverage, or other line-coverage collection despite the Zod Week 4 report
  retaining coverage as its final signal stage.
- Froze a post-hoc coverage-only supplement before execution. It reuses the
  same 23 immutable model responses and applies only to the two previously
  successful repairs; no decision or repair result can change.
- Pinned the reference procedure to Zod Week 4 commit `53aaeb99` and
  `dotnet-coverage` 18.9.0. Raw Cobertura output will remain temporary; only
  sanitized line summaries and logs will enter the archive.
- Mutation/Stryker remains excluded by Gary's explicit instruction.
- A pre-final dry run initially treated every upstream production path as a
  required coverage file. P-09 exposed that one candidate path has no net
  production diff in the validated repaired tree under the frozen target.
  Before the canonical run, the collector was corrected to the pinned Zod
  `compute-mutate.py` semantics: coverage scope is the net production diff
  from the frozen base. The generated dry-run coverage outputs were discarded;
  no model response, repair result, or original signal was changed.
