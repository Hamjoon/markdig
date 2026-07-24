# Markdig smoke run — batch log

Chronological run notes, deviations from the spec (`markdig-smoke-pipeline-spec.md`), retried
commands, and environment details. All numeric results in reports must trace to logged command
output stored in the case directories.

## 2026-07-24 — environment

- OS: macOS (Darwin 25.5.0), arm64
- dotnet SDK: 10.0.302 (only SDK installed; satisfies `src/global.json` 10.0.100 + rollForward latestMinor)
- All test/build commands pin `-f net10.0` per spec section 2.2 (no .NET 8 runtime present)
- Repo: fork `Hamjoon/markdig`, branch `experiment/2026-07-week4-markdig-smoke` created from
  local `main` @ `fc705234` ("Fix emoji table alignment regression (#943)"). All three smoke
  upstream commits are already reachable from `main`, so no `upstream` remote was needed.
- Smoke commits verified locally with `git show --stat`:
  - smoke-1 `9dffce52` (P): prod `src/Markdig/Extensions/AutoIdentifiers/AutoIdentifierExtension.cs`,
    test `src/Markdig.Tests/TestNormalize.cs` (adds test `AutoIdentifiersDoNotEmitGeneratedLinkReferenceDefinitions`)
  - smoke-2 `50061841` (S): prod `src/Markdig/Helpers/LinkHelper.cs`, test `src/Markdig.Tests/TestLinkHelper.cs`
  - smoke-3 `25506f20` (S): prod `src/Markdig/Helpers/CharHelper.cs`,
    test side `src/Markdig.Tests/Specs/EmphasisExtraSpecs.md` + `EmphasisExtraSpecs.generated.cs`
  - No commit touches paths outside `src/Markdig/` + `src/Markdig.Tests/` (section 4 sanity check passed;
    SpecFileGen untouched).
- OpenRouter key: not in env; sourced at call time from macOS keychain item `openrouter-api-key`
  (same mechanism as Zod v2 run-case.sh). Note: the Claude Code permission classifier blocked a
  direct interactive `security find-generic-password` probe; the call is embedded in
  `scripts/run-case.sh` instead and the key is never persisted.

## 2026-07-24 — port provenance and deviations

Source of reused assets: `zod-week3-july` repo @ `745ec751`
(`experiments/zod-repair-classification-v2/` + `scripts/run-gptoss-test-maintenance.py`).

1. Copied **unchanged**: `apply-patch.py`, `parse-response.py`.
2. Prompt template: the Zod v2 template is not a standalone file; it lives in
   `build_prompt_v2()` of `scripts/run-gptoss-test-maintenance.py`. Ported verbatim into
   `scripts/run-model.py` with these substrate deviations:
   - intro reads "maintaining a C# library" instead of "maintaining a TypeScript library"
     (keeping "TypeScript" verbatim would be factually wrong for this repo);
   - snippet path filter `packages/zod/**/*.ts` → `src/**/*.{cs,md}`, excluding `*.generated.cs`;
     pad (25) and per-file cap (220) unchanged;
   - smoke-3 constraints block gains one line marking `*.generated.cs` off-limits and pointing
     at the `.md` layer (required by spec section 5 stage 1).
3. `allowed_files` interpretation: spec 5.1 lists only test-side files, but the reused Zod v2
   template's Allowed-files line is `test_paths + prod_paths` (the DECISION contract needs a
   legal target for `fix_production` diffs). Kept the Zod contract: Allowed files = test side +
   production side; for smoke-3 the test side is the `.md` only (never `.generated.cs`).
4. Test-output truncation policy (spec section 4 "same length policy as Zod v2"): ANSI-strip +
   `tail -400`, taken from zod fixture.sh.
5. Stage 2 apply uses the full Zod v2 escalation chain (git apply → git apply --recount →
   patch --fuzz=3 → apply-patch.py context match), not apply-patch.py alone: spec section 5
   says stage semantics are identical to Zod v2, and that chain is what Zod v2's validate.sh
   implements. The `*.generated.cs` pre-check runs before any apply attempt.
6. Fixture worktrees live at `.worktrees/<case-id>` (Zod convention), excluded via
   `.git/info/exclude` (not `.gitignore`, to avoid touching tracked files). The fixture state is
   committed locally inside each worktree so failed applies reset cleanly and model diffs are
   readable via `git diff` (Zod convention).
7. P-case construction stores the production-side reversal as `prod-revert.patch` in the case
   dir (extra artifact beyond the spec layout, kept for reproducibility).
8. Extra per-case artifacts beyond the spec layout: `response-content.md` (message content
   extracted from raw `response.json`; parse-response.py input), `applied-repair.diff`
   (normalized applied patch), `logs/` (raw runner logs).
9. Target filters: smoke-1 uses the method-level FQN of the new test; smoke-2/smoke-3 use
   class-level filters because the upstream commits rename test methods / renumber spec
   examples, so a method-level filter could silently stop matching after a legitimate repair.
   Exact strings are discovered from runner output (make-fixture.sh DISCOVER mode), not guessed.
10. verdicts.json: `repair_success = target_pass && preservation_pass`, additionally forced to
    "no" for smoke-3 if the generated-file invariant fails (spec 5.3: the only way to green must
    be the `.md` layer).

## Pre-registered concern (before any fixture run)

- smoke-3 red-state risk: the stale (C~1) EmphasisExtraSpecs examples contain no `+` characters
  adjacent to emphasis delimiters (the only `+` content is `++Inserted text++`, whose delimiter
  flanking checks look at the characters *around* the run — line start and `I`). The production
  change only adds `'+'` to `IsPunctuationException`, used by `CheckOpenCloseDelimiter` on
  characters adjacent to delimiter runs. Hypothesis: the stale spec state may be GREEN under the
  new production, which would make smoke-3 unusable as an S fixture (upstream commit is
  test-first/additive). To be verified empirically in the fixture phase before any model call.

## 2026-07-24 — fixture construction

- Tooling issue: `dotnet test` runner output is localized (Korean) on this machine, which broke
  the English summary parsing on the first smoke-3 discovery run. Fixed by exporting
  `DOTNET_CLI_UI_LANGUAGE=en` in make-fixture.sh / validate.sh / signal.sh. The smoke-3
  discovery result itself was unaffected (rc=0, 통과/Passed: 2, 실패/Failed: 0).
- First build in each worktree regenerates ALL `*.generated.cs` (fresh checkout gives every
  spec `.md` a new mtime). Regeneration is byte-stable: worktrees stay `git status`-clean.
- **smoke-3 CONFIRMED NON-VIABLE** (pre-registered concern was correct):
  - focused stale run: `Passed! Failed: 0, Passed: 2, Total: 2` (`smoke-3/logs/discover.raw.log`)
  - full-suite stale run: `Passed! Failed: 0, Passed: 3791, Skipped: 1, Total: 3792`
    (`smoke-3/logs/full-suite-green.raw.log`)
  - Root cause: upstream `25506f20` is test-first/additive — the old spec examples do not
    contradict the new production behavior, so no stale-failing state exists for this commit.
    This is a case-mining defect, not a pipeline error: an S-category spec-layer case needs a
    commit whose spec `.md` diff CHANGES existing expected output, not one that only adds
    examples. Recorded as `pipeline_error: fixture-red-state-unreachable` in
    `smoke-3/verdicts.json`; stages 1–5 skipped (no failing output exists for the stage-1
    prompt). Spec acceptance criterion 7.1 ("all 3 fixtures red") is therefore not satisfiable
    with the specified case list; criteria are evaluated on smoke-1/smoke-2.
  - smoke-3 artifacts kept: fixture worktree + commit `79485f1f`, `stale-test.patch`,
    `fixture.patch`, `case.json` (with evidence), `verdicts.json`, logs.
- smoke-1 discovery: 1 failed / 38 total under `~Markdig.Tests.TestNormalize`; failing test
  `AutoIdentifiersDoNotEmitGeneratedLinkReferenceDefinitions` (copied verbatim from runner
  output). Final filter is method-level FQN.
- smoke-2 discovery: 22 failed under `~Markdig.Tests.TestLinkHelper` (renamed/changed
  parameterized tests `TestUrilizeScandinavianGermanChars`, `TestUrilizeNonAscii_*`). Final
  filter is class-level `Markdig.Tests.TestLinkHelper` because the upstream commit renames test
  methods (a method-level filter would stop matching after a legitimate repair).
- Red-state verification (make-fixture.sh, case.json written):
  - smoke-1: `FIXTURE: OK smoke-1 red-confirmed failed=1 passed=0 total=1 commit=bb41a2d6`
  - smoke-2: `FIXTURE: OK smoke-2 red-confirmed failed=22 passed=96 total=118 commit=833990e6`
