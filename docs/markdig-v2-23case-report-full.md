# GPT-OSS on Historical Test-Maintenance Fixtures in Markdig — Full Report (23 Cases)

This is the canonical detailed record of the Week 5 Markdig experiment: it
holds the execution details, per-case outcomes, and reproduction references
behind the [summary report](./markdig-v2-23case-report.md). All numbers and
verdicts in the two documents are identical; only the depth of explanation
differs.

## Public artifacts

- Subject project: [xoofx/markdig](https://github.com/xoofx/markdig) — a .NET/C# Markdown parser
- Artifact repository: [Hamjoon/markdig](https://github.com/Hamjoon/markdig) (fork; no upstream PR was opened)
- Archive branch (canonical): [experiment/2026-07-week5-markdig-30case-archive](https://github.com/Hamjoon/markdig/tree/experiment/2026-07-week5-markdig-30case-archive) — the orphan branch this report lives on, holding the per-case artifact packets that the case tables link to
- Case screening record: [markdig-23case-screening.md](markdig-23case-screening.md) (candidate pool, seeded queues, acceptance/rejection record)
- Fixture verification record: [markdig-23case-verification-results.md](markdig-23case-verification-results.md) (fresh reconstruction of all 23 fixtures before model execution)
- Pre-registered mining/screening protocol: [markdig-23case-protocol.md](markdig-23case-protocol.md)
- Model-run protocol: [markdig-23case-model-run-protocol.md](markdig-23case-model-run-protocol.md)
- Evaluation protocol: [markdig-23case-evaluation-protocol.md](markdig-23case-evaluation-protocol.md) (frozen decision, patch-application, preservation, and coverage rules)
- The complete execution history and raw screening/verification command logs remain on the full-history branch [experiment/2026-07-week5-markdig-30case](https://github.com/agent-eli/markdig/tree/experiment/2026-07-week5-markdig-30case)

## Terms used in this report

- **Recent change**: the single commit-derived diff applied on top of a base
  version of the repository to construct a case. It is the "most recent edit"
  the model is shown.
- **Fixture**: the prepared per-case source tree — the base version of the
  repository with the case's recent change applied. This is the state the
  model's repair is applied to and tested against.
- **Target tests**: the specific test filter each stale-test or
  production-regression case is evaluated on. Normal cases are evaluated on
  the full suite.
- **Failing / passing**: whether the tests fail or succeed when run. (These
  states are often called "red" and "green"; this report uses
  failing/passing.)
- **Upstream**: the original Markdig repository and its commit history, from
  which all cases were sampled.
- **Case ID**: `S`/`P`/`N` prefix plus a per-category number in acceptance
  order. Each case's position in the frozen screening queue is retained as
  `queue_id` in `cases.json`.

## Experiment question

Given a recent change diff, current test output, bounded relevant code
snippets, and an allowed-file list, can `openai/gpt-oss-120b`:

1. choose `fix_tests`, `fix_production`, or `no_change` correctly;
2. produce an allowed repair that applies under the established Zod cascade;
3. restore the required tests without undoing the intended recent change; and
4. preserve target-test line coverage of the net changed production path?

Expected decisions were frozen before model execution: S = `fix_tests`,
P = `fix_production`, N = `no_change`.

## Case composition and screening summary

Candidates came from non-merge Markdig commits dated from 2025-01-01 through
the frozen endpoint. Pre-registered mining applied source/test classification,
generated-file guards, size caps, duplicate controls, and a seeded category
shuffle. Empirical screening reconstructed historical states front-to-back
through each queue and required executable failing/passing conditions.

| Category | Intended state | Expected decision | Frozen cases |
|---|---|---|---:|
| S | Production changed; old tests fail | `fix_tests` | 3 |
| P | New tests fail against old production | `fix_production` | 10 |
| N | Production changed; full suite remains green | `no_change` | 10 |

S stopped at three because its complete 12-candidate queue was exhausted under
the frozen criteria. The window and criteria were not expanded. All 23
fixtures were independently reconstructed and reverified before model
execution with exact test-count and fixture-identity matches (see the fixture
verification record).

## Execution

- Candidate mining: `scripts/mine-candidates.py`
- Model run: `scripts/run-gptoss-test-maintenance.py`
- Signal evaluation: `scripts/run-markdig-signal-eval.py`
- Case metadata: `experiments/test-maintenance/cases.json`
- Model: `openai/gpt-oss-120b` (OpenRouter chat completions; temperature 0;
  one user message and one assistant response per case)
- Order: frozen manifest order, S then P then N
- Retries: transport-only when no assistant response exists
- Observed model calls: 23 primary trials, 0 retries, 0 errors

Each fixture pins its own build environment in `cases.json` (recorded .NET
SDK and target framework, `net9.0` or `net10.0` per case); every build and
test run of that case uses the pinned values.

## Prompt structure: template vs. per-case variables

The prompt sent to the model is assembled from a **fixed template** and
**per-case variables**. No part of the prompt names the case ID, category, or
expected decision, and every case uses the same template.

### Fixed template (identical across all 23 cases)

Intro (verbatim):

```text
You are maintaining a C#/.NET library. A change was recently applied to this repository.
Review the recent change and the current test results, then decide whether any modification
is needed: update tests, fix production code, or no change at all.
```

Constraints (verbatim; only the file list inside the third item varies per
case):

```text
- The first line of your reply must be exactly one of: `DECISION: no_change`,
  `DECISION: fix_tests`, `DECISION: fix_production`.
- If the decision is `fix_tests` or `fix_production`, follow the DECISION line with a
  unified diff implementing the fix. If the decision is `no_change`, output no diff.
- Allowed files: <per-case file list>.
- Do not weaken, delete, or skip assertions.
- Preserve nearby behavior that is still expected to pass.
```

The response protocol is part of the template: the first line must be a
`DECISION`, and a unified diff follows only for `fix_tests` /
`fix_production`.

### Per-case variables

| Variable | Content | Producer |
| --- | --- | --- |
| Allowed-files list | The case's test and production file paths (inserted into the fixed constraints block) | `cases.json` |
| `<recent_change_diff>` | The path-restricted diff applied to the fixture (stale-test and normal cases: the upstream production diff; production-regression cases: the new-test diff) | fixture construction |
| `<test_output>` | The frozen test run output on the fixture (stale-test and production-regression cases: the failing target output; normal cases: the passing full-suite summary) | fixture verification |
| `<test_snippet>` / `<production_snippet>` | Code around the changed regions of the diff, ±25 lines of padding, at most 220 lines per file; each snippet is tagged with its `path` and `lines` attributes and read from the exact revision the fixture state represents | snippet extractor (`prepare-model-runs.py`) |

Normal cases carry no test snippet (their diff touches no test file). Every
prompt actually sent is archived per case as `gptoss-prompt.md`, so the exact
template/variable instantiation of any case can be inspected directly.

## Case-level pipeline

Each case runs through these stages. A case exits at the first stage it
fails; the binary repair judgment (below) is defined by how far a case gets.

1. **Decision** — the model's response to the single request; the first-line
   `DECISION` is compared with the expected response for the category.
2. **Patch apply** — the model's diff is attempted from the identical
   committed fixture state by a four-method cascade: ordinary `git apply`,
   `git apply --recount`, GNU/BSD `patch` with fuzz 3, then the Zod context
   matcher, which locates unchanged pre-images and tolerates bare or
   inaccurate hunk coordinates.
3. **Allowed-path enforcement** — after a successful application, Git derives
   the actual changed paths, which must be non-empty, inside the frozen
   allowed list, on the side named by the decision, and free of generated C#
   files.
4. **Validation** — the project is rebuilt with the pinned SDK/TFM; S/P target
   tests and the full suite must pass, non-empty.
5. **Preservation check** — `git apply --reverse --check fixture.patch` on the
   repaired tree verifies that the complete intended recent change remains
   present. A passing tree that fails this check reached passing by reverting
   the intended change.
6. **Signal (coverage)** — for repairs that pass stages 2–5, the frozen target
   filter is rerun with coverage collection to confirm the tests still
   execute the net changed production file.

## Binary repair judgment

- **Patch applied** means the unedited extracted code was applied by the
  first successful method in the Zod cascade and changed only frozen allowed
  paths.
- **Behavior validation** requires a successful build, a passing non-empty
  target for S/P, and a passing non-empty full suite.
- **Repair success (Repair = yes)** requires patch application, behavior
  validation, and preservation of the complete recent fixture change.
  **Repair = no** covers everything else: a non-applying patch, build/test
  failure, or a passing tree that removed part of the recent change.
- **Strict signal success** requires the exact expected decision and a
  successful corresponding action. Correct N decisions require a passing full
  suite and preservation; S/P decisions require repair success and file-level
  target-test coverage over the validated tree's net production diff.

Mutation testing is excluded by instruction; no mutation score or
mutation-derived judgment is reported.

## Aggregate results

| Metric | Overall | S | P | N |
|---|---:|---:|---:|---:|
| Cases | 23 | 3 | 10 | 10 |
| Exact decision | 17/23 (73.9%) | 0/3 (0.0%) | 10/10 (100.0%) | 7/10 (70.0%) |
| Response-shape contract | 23/23 (100.0%) | 3/3 | 10/10 | 10/10 |
| Patch applied | 13/16 (81.3%) | 2/3 | 8/10 | 3/3 fix responses |
| Behavior validation | 12/23 (52.2%) | 0/3 | 2/10 | 10/10 |
| Successful required repair | 2/13 (15.4%) | 0/3 | 2/10 | not applicable |
| Strict signal success | 9/23 (39.1%) | 0/3 (0.0%) | 2/10 (20.0%) | 7/10 (70.0%) |
| Coverage signal | 2/2 (100.0%) | not applicable | 2/2 | not applicable |

Exact decision agreement was 17/23 cases (73.9%). Pipeline errors: 0.
Infrastructure retries: 0. All 23 cases completed on the first infrastructure
attempt.

## Decision matrix

| Expected | Predicted `fix_tests` | Predicted `fix_production` | Predicted `no_change` |
|---|---:|---:|---:|
| `fix_tests` | 0 | 3 | 0 |
| `fix_production` | 0 | 10 | 0 |
| `no_change` | 0 | 3 | 7 |

The model never selected `fix_tests`; it chose `fix_production` for all S and
P cases and for three N cases.

## Patch application under the Zod-equivalent cascade

All 16 fix responses contained code after a valid first-line decision. As in
the Zod experiment, their diffs were not standard-format and required the
context-matching fallback. This format detail is not scored separately.

Each fix was tried from the identical committed fixture state:

1. `git apply --whitespace=nowarn`: 0/16
2. `git apply --whitespace=nowarn --recount`: 0/16
3. `patch -p1 --forward --fuzz=3 --no-backup-if-mismatch`: 0/16
4. Zod-style context matching: 13/16

The successful 13 normalized repairs all changed non-empty, frozen allowed
paths on the side named by the response. S-01, P-04, and P-07 matched no
candidate pre-image and remained non-applying. Application succeeded for
**13/16 responses (81.3%)**.

## Per-case results

| Case | Expected | Predicted | Decision correct | Apply method | Behavior valid | Preserved | Repair success | Strict signal | Outcome |
|---|---|---|---:|---|---:|---:|---:|---:|---|
| S-01 | fix_tests | fix_production | no | n/a | no | no | no | no | model-patch-does-not-apply |
| S-02 | fix_tests | fix_production | no | context-match | no | no | no | no | build-failed-after-model-action |
| S-03 | fix_tests | fix_production | no | context-match | no | no | no | no | build-failed-after-model-action |
| P-01 | fix_production | fix_production | yes | context-match | no | yes | no | no | executable-validation-failed |
| P-02 | fix_production | fix_production | yes | context-match | yes | yes | yes | yes | signal-pass |
| P-03 | fix_production | fix_production | yes | context-match | no | yes | no | no | executable-validation-failed |
| P-04 | fix_production | fix_production | yes | n/a | no | no | no | no | model-patch-does-not-apply |
| P-05 | fix_production | fix_production | yes | context-match | yes | yes | yes | yes | signal-pass |
| P-06 | fix_production | fix_production | yes | context-match | no | yes | no | no | executable-validation-failed |
| P-07 | fix_production | fix_production | yes | n/a | no | no | no | no | model-patch-does-not-apply |
| P-08 | fix_production | fix_production | yes | context-match | no | yes | no | no | executable-validation-failed |
| P-09 | fix_production | fix_production | yes | context-match | no | yes | no | no | executable-validation-failed |
| P-10 | fix_production | fix_production | yes | context-match | no | yes | no | no | build-failed-after-model-action |
| N-01 | no_change | no_change | yes | n/a | yes | yes | no | yes | signal-pass |
| N-02 | no_change | fix_production | no | context-match | yes | no | no | no | recent-change-not-preserved |
| N-03 | no_change | no_change | yes | n/a | yes | yes | no | yes | signal-pass |
| N-04 | no_change | no_change | yes | n/a | yes | yes | no | yes | signal-pass |
| N-05 | no_change | no_change | yes | n/a | yes | yes | no | yes | signal-pass |
| N-06 | no_change | fix_production | no | context-match | yes | no | no | no | recent-change-not-preserved |
| N-07 | no_change | no_change | yes | n/a | yes | yes | no | yes | signal-pass |
| N-08 | no_change | no_change | yes | n/a | yes | yes | no | yes | signal-pass |
| N-09 | no_change | fix_production | no | context-match | yes | no | no | no | recent-change-not-preserved |
| N-10 | no_change | no_change | yes | n/a | yes | yes | no | yes | signal-pass |

## Successful repairs

Two required P repairs succeeded end to end:

- **P-02** (block-attribute leading newline): context-applied to
  `GenericAttributesParser.cs`; target 4/4 passed; full suite 3,551 passed,
  1 skipped, 0 failed; recent change preserved.
- **P-05** (CodeInlineParser bounds handling): context-applied to
  `CodeInlineParser.cs`; target 46/46 passed; full suite 3,552 passed,
  1 skipped, 0 failed; recent change preserved.

Of the 13 cases that required a fix, these two are the only end-to-end
successes: **2/13 required repairs (15.4%)**.

## Coverage Signal

Coverage applies only after patch application, target validation, and
preservation have all succeeded. Each successful case was reconstructed from
its frozen base, fixture, and archived normalized repair. The frozen target
was revalidated and then run with the Markdig Week 4 Microsoft.NET.Test.Sdk
built-in collector using
`dotnet test --collect:"Code Coverage;Format=cobertura"`. The resulting XML
was parsed by a byte-identical copy of Week 4 `parse-cobertura.py`. Raw
Cobertura XML remained temporary because it contains local source paths.

| Case | Target recheck | Net production scope | Line coverage | Coverage verdict |
|---|---:|---|---:|---|
| P-02 | 4/4 | `src/Markdig/Extensions/GenericAttributes/GenericAttributesParser.cs` | 108/115 (93.91%) | signal preserved |
| P-05 | 46/46 | `src/Markdig/Parsers/Inlines/CodeInlineParser.cs` | 63/66 (95.45%) | signal preserved |

The scope is derived from the validated repaired tree's net production diff
against the frozen base, matching Zod's `compute-mutate.py` semantics. For
P-05, `src/Markdig/Polyfills/SpanExtensions.cs` was a frozen upstream
candidate but had no net diff after the model's alternative repair and is
inactive under the frozen `net9.0` target. It is retained in the summary as an
excluded candidate rather than treated as a missing covered file.

Coverage verdicts were therefore signal-preserved for **2/2 applicable
repairs**, with zero weakened or unknown cases. Strict signal success,
including coverage, is **9/23 (39.1%)**.

Coverage percentages are file-level. They confirm the changed file is
exercised by the target tests; they do not by themselves measure how well the
tests would detect future bugs (see Limitations).

## Key finding: validation is incomplete without the preservation check

The three N false-positive patches (N-02, N-06, N-09) applied, built, and left
the full suite passing. Looking at test results alone, they are
indistinguishable from harmless edits. However, each failed
`git apply --reverse --check fixture.patch`: it removed or altered the
intended recent production change. They are not successful actions. This is
exactly the false-passing condition that the preservation gate adopted from
the Zod experiment is designed to catch, and it reproduced on a second
repository and language. All eight applied P patches, by contrast, preserved
the recent test-oracle change — on the P side the failure modes were
executable, not preservational.

## Failure notes per case (Repair = no, 11 required-repair cases)

All three stale-test cases point in the same direction the Zod experiment
observed — treating the tests as the specification and the recent production
change as the bug — but here the direction was total: `fix_tests` was never
chosen.

Patch apply failures (3):

- **S-01** (link-helper ASCII normalization): the model rewrote the
  normalization block in `LinkHelper.cs` assuming the pre-change shape of the
  code (including a special-character branch the recent change had replaced);
  no contiguous pre-image existed in the fixture, so even context-matching
  application was impossible.
- **P-04** (indented and zero blocks): the diff targeted the roundtrip
  `ListRenderer.cs` but removed a code block that does not exist in that
  shape in the fixture; no candidate pre-image matched.
- **P-07** (HTML `search` tag support): the diff edited the
  `HtmlBlockParser.cs` prefix-tree table (capacity 66→67 plus a `search`
  entry) but assumed table content outside the provided snippet; no
  contiguous pre-image matched.

Applied but the build failed (3):

- **S-02** (abbreviation emphasis resolution): the context-applied edit to
  `AbbreviationParser.cs` inverted a null-guard (`is not null` → `is null` +
  `continue`) while restructuring the block; the project did not compile.
  The tree also failed the preservation check.
- **S-03** (span validation/update APIs): the context-applied edit rewrote
  the definition-item span computation in `DefinitionListParser.cs`; the
  project did not compile. The tree also failed the preservation check.
- **P-10** (blockquote ordered-list parsing): the context-applied edit to
  `ListBlockParser.cs` did not compile.

Applied and built, but tests still failing (5):

- **P-01** (table without preceding blank line): edit to
  `PipeTableParser.cs`; target 9 failing; full suite 43 failing — the
  attempted parser change broke unrelated table behavior.
- **P-03** (CJK emphasis after entity newline): edit to
  `EmphasisInlineParser.cs`; target 3 failing; full suite 5 failing.
- **P-06** (pipe-table unmatched subscript): edit to `PipeTableParser.cs`;
  target 1 failing; full suite 10 failing.
- **P-08** (autolink URL roundtrip): edit to the roundtrip
  `LinkInlineRenderer.cs`; target 3 failing; full suite 3 failing.
- **P-09** (pipe table after leading paragraph): edit to
  `PipeTableParser.cs`; target 2 failing; full suite 2 failing.

Unnecessary edits on normal cases (3; not counted in required repairs):

- **N-02** (AutoLinkParser false-positive overhead): the model judged the
  recent change's `StringComparison.Ordinal` scheme checks a bug and switched
  them back to `OrdinalIgnoreCase` — undoing the intended optimization. Full
  suite passing; preservation check failed.
- **N-06** (empty-stack PopIndent error): the model removed the
  `InvalidOperationException` the recent change had introduced in
  `TextRendererBase.PopIndent()`, restoring the earlier tolerant behavior — a
  direct inversion of the intended change. Full suite passing; preservation
  check failed.
- **N-09** (DefinitionListParser exception): the model rewrote the
  switch-based block handling the recent change had introduced in
  `DefinitionListParser.cs`. Full suite passing; preservation check failed.

## Run notes

- Model output diffs are not standard-format: 0/16 applied under plain
  `git apply`, `--recount`, or `patch --fuzz=3`; all 13 applications came
  from the context-matching applier. Measured repair success is therefore
  sensitive to the applier's tolerance, as in the Zod experiment.
- The evaluator is pinned to the public Zod Week 4 application and validation
  sources by commit (`53aaeb99`) and SHA-256; the coverage collector and
  parser are pinned to Markdig Week 4 by commit (`caf6195e`) and SHA-256 (see
  the evaluation protocol).
- Every apply attempt starts from an identical committed fixture state; after
  application, Git derives and enforces the actual changed paths against the
  frozen allowed list.
- Each case builds and tests with its pinned .NET SDK and target framework
  (`net9.0` or `net10.0`) recorded in `cases.json`.
- Zero transport retries and zero pipeline errors were observed across all 23
  calls.

## Archive layout

Artifacts are preserved on an orphan archive branch that does not inherit the
Markdig source tree. Each case lives under
`experiments/test-maintenance/cases/<case>-<sha8>/`, matching the
case-centered layout of the preceding Zod experiment, and contains:

- `fixture.patch` (the recent change applied to the base), `test-output.txt`
  (test state given to the model), `input.json` (immutable input digests and
  revision/path metadata)
- `gptoss-prompt.md`, `gptoss-response.md`, `gptoss-usage.json`,
  `gptoss-run.json` (immutable model exchange and API metadata)
- `gptoss-repair.patch` (model's raw diff), `applied-repair.diff` (normalized
  post-apply diff), `validation.log`, `result.json`
- `coverage/` (sanitized coverage summary and execution log, successful
  repairs only)

The three canonical aggregate JSON artifacts are `cases.json`,
`results-summary.json`, and `screening_queues.json`;
`metadata/experiment.json` holds the compact mining, screening, and
fixture-verification provenance. `audit.py` re-derives and reconciles the
records end to end.

## Usage

```json
{
  "prompt_tokens": 75626,
  "completion_tokens": 34534,
  "total_tokens": 110160,
  "cost": 0.011487683
}
```

(23 calls — one per case, no retries. Cost in USD as reported by the API.)

## Integrity audit

- Raw response hashes still match the immutable model-run records.
- Every fix response was attempted by all four methods through the first
  success; every successful repair is stored as a normalized Git diff.
- All 13 applied repair diffs change only frozen allowed paths and no
  generated C# file.
- Preservation was independently reconstructed from base + fixture +
  normalized repair for all 20 evaluable actions; all recomputed results
  match the records.
- Stored test counts were re-parsed from sanitized logs; correct N no-change
  counts also match the earlier fixture verification exactly.
- All temporary worktrees were removed and the evidence scan found no local
  path, credential, username, hostname, or workspace identifier.
- The two coverage summaries reproduce the frozen target counts, identify two
  covered net production scopes, and contain no raw Cobertura, `.coverage`,
  or machine-specific path artifact.

## Interpretation

1. **The stale-test direction was never chosen.** The model chose
   `fix_production` on all three stale-test cases and on three normal cases;
   errors flowed only toward "doubt the recent production change". The Zod
   experiment saw the same directionality at 5/10 on its stale-test side;
   here, with a smaller S denominator, the collapse was complete.
2. **The preservation gate is what separates real success from
   false-passing.** Three normal-case edits left the whole suite passing
   while silently reverting the intended change — invisible to any
   passing-only criterion, caught mechanically by the reverse-apply check.
3. **Repair execution, not patch text, was the bottleneck.** The model's code
   applied in 81.3% of fix responses under the established tolerance policy,
   but only 2 of 13 required repairs survived build, tests, and preservation.
   The decisive gap was semantic and directional repair quality, not raw
   patch applicability.
4. **Decision accuracy overstates end-to-end performance.** Exact decision
   accuracy (73.9%) exceeded strict signal success (39.1%) by 34.8 percentage
   points. Patch syntax, patch application, classification, behavioral
   validation, and change preservation must remain separate measurements.

## Limitations

- Only three S fixtures satisfied the frozen selection criteria, so
  stale-test conclusions have a small denominator.
- This is one repository, one historical window, one model configuration, and
  one trial per case.
- Context matching is intentionally more permissive than standard patch
  parsing. Its outputs are therefore retained as normalized Git diffs, and
  actual changed paths are checked after application.
- The preservation check is mechanical and exact: it establishes that the
  complete fixture patch remains reverse-applicable, not broader semantic
  equivalence.
- Passing target and full suites do not prove correctness outside tested
  behavior.
- Coverage runs only the frozen target filter. It confirms execution of each
  net changed production file, not complete branch coverage or causal
  adequacy of every changed line.
- Mutation testing was out of scope, so this experiment does not estimate
  assertion strength against injected faults.
