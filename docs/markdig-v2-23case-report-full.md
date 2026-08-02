# Markdig Week 5 GPT-OSS Repair and Signal Evaluation

## Scope and Definitions

The fixture set contains 3 stale-test cases (S), 10 production-regression
cases (P), and 10 no-change cases (N). Expected decisions were frozen before
model execution: S = `fix_tests`, P = `fix_production`, and N = `no_change`.

- **Patch applied** means the unedited extracted code was applied by the first
  successful method in the Zod cascade and changed only frozen allowed paths.
- **Behavior validation** requires a successful build, a green non-empty
  target for S/P, and a green non-empty full suite.
- **Repair success** requires patch application, behavior validation, and
  preservation of the complete recent fixture change.
- **Strict signal success** requires the exact expected decision and a
  successful corresponding action. Correct N decisions require a green full
  suite and preservation; S/P decisions require repair success and file-level
  target-test coverage over the validated tree's net production diff.

Mutation testing is excluded by instruction.

## Aggregate Results

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

Pipeline errors: 0. Infrastructure retries: 0. All 23 cases completed on the
first infrastructure attempt.

## Decision Matrix

| Expected | Predicted `fix_tests` | Predicted `fix_production` | Predicted `no_change` |
|---|---:|---:|---:|
| `fix_tests` | 0 | 3 | 0 |
| `fix_production` | 0 | 10 | 0 |
| `no_change` | 0 | 3 | 7 |

The decision score remains 17/23 (73.9%). The model never selected
`fix_tests`; it chose `fix_production` for all S and P cases and for three N
cases.

## Zod-Equivalent Patch Application

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

## Repair and Preservation Outcomes

Two required P repairs succeeded end to end:

- **P-02**: context-applied to
  `GenericAttributesParser.cs`; target 4/4 passed; full suite 3,551 passed,
  1 skipped, 0 failed; recent change preserved.
- **P-05**: context-applied to `CodeInlineParser.cs`; target 46/46 passed;
  full suite 3,552 passed, 1 skipped, 0 failed; recent change preserved.

The other required fixes failed as follows:

- S-01, P-04, P-07: patch did not apply after all four methods.
- S-02, S-03, P-10: context application succeeded, but the resulting project
  did not build. S-02 and S-03 also failed the preservation check.
- P-01: target 9 failed; full suite 43 failed.
- P-03: target 3 failed; full suite 5 failed.
- P-06: target 1 failed; full suite 10 failed.
- P-08: target 3 failed; full suite 3 failed.
- P-09: target 2 failed; full suite 2 failed.

All eight applied P patches preserved the recent test-oracle change. Only
P-02 and P-05 also restored both required test scopes, producing **2/13
(15.4%) successful required repairs**.

The three N false-positive patches (N-02, N-06, N-09) applied, built, and left
the full suite green. However, each failed
`git apply --reverse --check fixture.patch`: it removed or altered the intended
recent production change. They are not successful actions. This is exactly the
false-green condition that Zod's preservation gate is designed to catch.

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

## Per-Case Results

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

## Integrity Audit

- Raw response hashes still match the immutable model-run records.
- Every fix response was attempted by all four methods through the first
  success; every successful repair is stored as a normalized Git diff.
- All 13 applied repair diffs change only frozen allowed paths and no generated
  C# file.
- Preservation was independently reconstructed from base + fixture +
  normalized repair for all 20 evaluable actions; all recomputed results match
  the records.
- Stored test counts were re-parsed from sanitized logs; correct N no-change
  counts also match the earlier fixture verification exactly.
- All temporary worktrees were removed and the evidence scan found no local
  path, credential, username, hostname, or workspace identifier.
- The two coverage summaries reproduce the frozen target counts, identify two
  covered net production scopes, and contain no raw Cobertura, `.coverage`, or
  machine-specific path artifact.

## Interpretation

GPT-OSS supplied context-applicable code in 13/16 fix responses, but only two
of the 13 required S/P repairs passed preservation and executable validation.

Exact decision accuracy still overstates end-to-end performance: 73.9% versus
39.1% strict signal success. The 34.8-point gap reflects semantic repair,
build/test, and preservation failures.

The coverage result confirms that both successful repairs execute their net
changed production file under the frozen target tests. File-level line
coverage does not establish complete behavioral adequacy or causal coverage of
every changed line.
