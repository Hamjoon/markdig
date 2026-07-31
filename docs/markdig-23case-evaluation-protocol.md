# Markdig Week 5 Zod-Equivalent Repair and Signal Evaluation Protocol

## Scope

This protocol evaluates the 23 frozen GPT-OSS responses without editing a
response, adding hunk coordinates, or manually repairing model code. Patch
application and validation are mechanical and deterministic.

Mutation testing remains excluded by instruction. No Stryker command or
mutation-derived metric is part of this gate.

## Zod Reference

The application and preservation procedure is pinned to Zod branch
`experiment/2026-07-week4` at commit
`53aaeb99d50a253d83f5dc18791b118c480ea8db`:

- `experiments/test-maintenance/apply-patch.py` SHA-256
  `4579a1eaa70bcf5ea31cf1b1fa3c2c39ac237a1d9fbb2438394b817c395ac7ef`
- `experiments/test-maintenance/validate.sh` SHA-256
  `f4190de97b2894465825acad70ed85c3446732894690c0630fc6bec4f7bc5d1b`

The local `context_apply.py` preserves Zod's matching order: exact pre-image,
trailing-whitespace-insensitive pre-image, then fully stripped pre-image. A
headerless section is assigned to the first frozen candidate file whose
pre-image matches every hunk. The local adaptation additionally rejects
absolute/traversal paths and targets outside the frozen candidate list.

## Expected Decisions

The expected decision remains fixed by category:

- S: `fix_tests`
- P: `fix_production`
- N: `no_change`

Exact-decision accuracy, patch application, repair success, and strict signal
success are reported separately.

## Response Extraction

1. Read the recorded first line and map the three allowed `DECISION:` values.
2. For `no_change`, require the remaining response body to be empty.
3. For a fix decision, use the single fenced code block when exactly one is
   present; otherwise use the body after the decision line.
4. Retain the extracted patch byte-for-byte.
5. Preserve format details as machine-readable audit metadata, but do not use
   them as an application gate or a professor-facing performance metric.
6. Reject an explicit unsafe or out-of-fixture header path before execution.

## Fixture and Four-Stage Apply Cascade

Each case starts at its frozen `base_sha` in a detached worktree. The stored
`fixture.patch` is applied and committed locally in that worktree so every
application method can start from the identical fixture state.

Every fix response is tried in this fixed order, resetting the worktree to the
fixture commit before each method:

1. `git apply --whitespace=nowarn`
2. `git apply --whitespace=nowarn --recount`
3. `patch -p1 --forward --fuzz=3 --no-backup-if-mismatch`
4. `context_apply.py`, the Zod-style pre-image matcher

The first successful method wins. After it succeeds, the evaluator derives
the actual changed paths from Git, requires a non-empty change, rejects
generated C# files, and requires all paths to be in the frozen per-case
production/test/spec candidate set. It also records whether the actual paths
agree with the side named by the model's decision. The normalized applied
repair is retained as a Git diff against the fixture commit.

## Validation and Recent-Change Preservation

After the model action:

1. Run `git apply --reverse --check fixture.patch` on the resulting tree. As
   in Zod Week 4, success means the complete recent change is still present.
2. Build `src/Markdig.Tests/Markdig.Tests.csproj` in Release mode for the
   frozen target framework.
3. For S and P, run the frozen non-empty target filter.
4. Run the non-empty full `Markdig.Tests` suite for every case.

The preservation result is recorded even when a later build or test fails. A
passing tree that cannot reverse-check the fixture is not a successful repair:
it made the tests pass by removing or altering part of the intended recent
change.

## Metrics

- Exact-decision accuracy overall and by S/P/N.
- Response-shape contract: valid first line plus an empty body for
  `no_change`, or a present patch for a fix decision.
- Application attempt and success rates, method distribution, actual scope,
  and decision-side agreement.
- Build, target-test, full-suite, and recent-change-preservation outcomes.
- **Repair success for a fix response:** scoped patch applied, build and
  required tests passed, and the recent change was preserved.
- **Strict signal success:** the expected decision was selected and the
  corresponding action succeeded. A correct `no_change` requires a green full
  suite and preservation; a fix requires repair success.

A non-standard model diff can therefore demonstrate a repair when the frozen
Zod-equivalent cascade applies its code unchanged.

## Infrastructure Retry and Evidence

An invalid/non-applying model patch, build failure, test failure, or
preservation failure is an observed outcome and is not retried. Only a
worktree/tool timeout or unparseable runner output is a pipeline error; it may
be retried once from scratch, with both attempt records retained.

Per case, retain the raw-response hash, extracted patch, all four application
attempts until first success, normalized applied diff, actual paths,
preservation result, sanitized logs, test counts, and final flags. Reconcile
the aggregate JSON and English reports, commit locally, and stop. Publication
requires a separate explicit approval after the evaluation is complete.

## Coverage Signal Protocol

Coverage applies only to cases whose repair passed patch application, target
validation, and recent-change preservation. The collection and parsing path
is pinned to Markdig Week 4 commit
`caf6195e3c3a25b3b153329cb29ae7270bce5b57`: `signal.sh` SHA-256
`acdf6b3ca65f8cf3d9ad45e4ddedfea7c7f0d504c07e3da857e99db0a75273cf`
and byte-identical `parse-cobertura.py` SHA-256
`622740d5aabcbd282d6680230cfa2cc3bcde5a41ad8006d530a93507453a6e18`.

For each successful repair:

1. Reconstruct the frozen base, apply and commit `fixture.patch`, then apply
   the archived normalized `applied-repair.diff` without inference.
2. Recheck the frozen target counts and `git apply --reverse --check` fixture
   preservation.
3. Run only the frozen target filter with the Microsoft.NET.Test.Sdk built-in
   collector: `dotnet test --collect:"Code Coverage;Format=cobertura"`. No
   project-file modification is made.
4. Match Zod's production-scope rule: form candidates from the frozen
   `prod_src_files` plus the model repair's actual production paths, then keep
   only files present in the validated repaired tree's net diff from the
   frozen base. Record excluded candidates and their reason.
5. Run the pinned `scripts/parse-cobertura.py` against the temporary Cobertura
   XML and every in-scope production file. Retain its `lines_covered`,
   `lines_valid`, and `covered` fields without reinterpretation.
6. Mark the case `signal_preserved` only when every in-scope production file is
   present in the report and has at least one covered line. A present file with
   zero covered lines is `signal_weakened`; missing or failed tooling is
   `signal_unknown`.

Raw Cobertura XML is not archived because it contains machine-specific source
paths. Only a path-sanitized per-case summary and execution log are retained.
Cases without a successful repair are not rerun for coverage; their existing
failure/no-change status is recorded explicitly as non-applicable,
`partial_repair`, or `signal_unknown`. Mutation testing remains excluded by
instruction.
