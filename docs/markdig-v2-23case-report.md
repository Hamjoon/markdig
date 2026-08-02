# GPT-OSS on Historical Test-Maintenance Fixtures in Markdig

## Executive Summary

This Week 5 experiment tested whether `openai/gpt-oss-120b` could distinguish
three maintenance situations in Markdig and return a successful action:

- stale tests that should be updated (S),
- production regressions exposed by new tests (P), and
- already-correct changes requiring no action (N).

The frozen dataset contained 23 cases: S=3, P=10, N=10. GPT-OSS made the exact
decision in **17/23 cases (73.9%)**. Under the established patch-application,
recent-change-preservation, and coverage procedure, strict signal success was
**9/23 (39.1%)**: two successful P repairs with preserved coverage and seven
correct N no-change actions.

The model diffs were not standard-format, so the Zod-style context matcher was
needed. It applied 13/16 without editing model code, while successful required
repair was rare: **2/13 required repairs (15.4%)**.

The two successful repairs both covered their net changed production file
under the frozen target tests, so both satisfy the coverage signal gate.

## Research Question

Given a recent change diff, current test output, bounded relevant code
snippets, and an allowed-file list, can GPT-OSS:

1. choose `fix_tests`, `fix_production`, or `no_change` correctly;
2. produce an allowed repair that applies under the established Zod cascade;
3. restore the required tests without undoing the intended recent change; and
4. preserve target-test line coverage of the net changed production path?

## Dataset Construction

Candidates came from non-merge Markdig commits dated from 2025-01-01 through
the frozen endpoint. Pre-registered mining applied source/test classification,
generated-file guards, size caps, duplicate controls, and a seeded category
shuffle. Empirical screening reconstructed historical states and required
executable failing/passing conditions.

| Category | Intended state | Expected decision | Frozen cases |
|---|---|---|---:|
| S | Production changed; old tests fail | `fix_tests` | 3 |
| P | New tests fail against old production | `fix_production` | 10 |
| N | Production changed; full suite remains green | `no_change` | 10 |

S stopped at three because its complete 12-candidate queue was exhausted under
the frozen criteria. The window and criteria were not expanded. All 23
fixtures were independently reconstructed and reverified before model
execution with exact test-count and fixture-identity matches.

## Model Protocol

- Model: `openai/gpt-oss-120b`
- API: OpenRouter chat completions
- Temperature: 0
- Trials: one independent user message and one assistant response per case
- Order: frozen manifest order, S then P then N
- Retries: transport-only when no assistant response exists
- Observed model calls: 23 primary trials, 0 retries, 0 errors

Each prompt included the fixture's recent-change diff, frozen test output,
bounded snippets, and allowed paths. It did not expose the category or
expected decision. A fix decision required code in diff form.

The 23 calls used 75,626 prompt tokens and 34,534 completion tokens (110,160
total). The API-reported aggregate cost was USD 0.011487683.

## Evaluation Procedure

Each fix response was evaluated through this cascade from an identical
committed fixture state before every attempt:

1. ordinary `git apply`;
2. `git apply --recount`;
3. GNU/BSD `patch` with fuzz 3;
4. the Zod context matcher, which locates unchanged pre-images and tolerates
   bare or inaccurate hunk coordinates.

After a successful application, Git derived and enforced the actual allowed
paths. The project was rebuilt; S/P target tests and the full suite were run;
then `git apply --reverse --check fixture.patch` verified that the intended
recent change remained present.

## Results

**Repair** is a binary outcome: **yes** means the model action applied, the
target and full test suites passed, and the complete recent change remained
present. **No** covers a non-applying patch, build/test failure, or a passing
tree that removed part of the recent change.

### Case Matrix — stale-test cases (expected DECISION: fix_tests)

| ID | Base | Recent change | DECISION | Repair |
|---|---|---|---|---|
| [S-01](../experiments/test-maintenance/cases/s01-12590e5f/) | [8c01cf05](https://github.com/xoofx/markdig/commit/8c01cf05) | [12590e5f](https://github.com/xoofx/markdig/commit/12590e5f) link-helper ASCII normalization | fix_production ❌ | no |
| [S-02](../experiments/test-maintenance/cases/s02-5365879a/) | [a9bd7c6a](https://github.com/xoofx/markdig/commit/a9bd7c6a) | [5365879a](https://github.com/xoofx/markdig/commit/5365879a) abbreviation emphasis resolution | fix_production ❌ | no |
| [S-03](../experiments/test-maintenance/cases/s03-148fd08b/) | [c488a274](https://github.com/xoofx/markdig/commit/c488a274) | [148fd08b](https://github.com/xoofx/markdig/commit/148fd08b) span validation/update APIs | fix_production ❌ | no |

### Case Matrix — production-regression cases (expected DECISION: fix_production)

| ID | Base | Recent change | DECISION | Repair |
|---|---|---|---|---|
| [P-01](../experiments/test-maintenance/cases/p01-d548b82b/) | [7ff8db90](https://github.com/xoofx/markdig/commit/7ff8db90) | [d548b82b](https://github.com/xoofx/markdig/commit/d548b82b) table without preceding blank line | fix_production ✅ | no |
| [P-02](../experiments/test-maintenance/cases/p02-781d9b53/) | [54357022](https://github.com/xoofx/markdig/commit/54357022) | [781d9b53](https://github.com/xoofx/markdig/commit/781d9b53) block-attribute leading newline | fix_production ✅ | **yes** |
| [P-03](../experiments/test-maintenance/cases/p03-fcbf8170/) | [5dca4149](https://github.com/xoofx/markdig/commit/5dca4149) | [fcbf8170](https://github.com/xoofx/markdig/commit/fcbf8170) CJK emphasis after entity newline | fix_production ✅ | no |
| [P-04](../experiments/test-maintenance/cases/p04-5a3c2060/) | [682c7272](https://github.com/xoofx/markdig/commit/682c7272) | [5a3c2060](https://github.com/xoofx/markdig/commit/5a3c2060) indented and zero blocks | fix_production ✅ | no |
| [P-05](../experiments/test-maintenance/cases/p05-800235ba/) | [d5f8a809](https://github.com/xoofx/markdig/commit/d5f8a809) | [800235ba](https://github.com/xoofx/markdig/commit/800235ba) CodeInlineParser bounds handling | fix_production ✅ | **yes** |
| [P-06](../experiments/test-maintenance/cases/p06-0f98267a/) | [fcbf8170](https://github.com/xoofx/markdig/commit/fcbf8170) | [0f98267a](https://github.com/xoofx/markdig/commit/0f98267a) pipe-table unmatched subscript | fix_production ✅ | no |
| [P-07](../experiments/test-maintenance/cases/p07-b15cf582/) | [61e9be29](https://github.com/xoofx/markdig/commit/61e9be29) | [b15cf582](https://github.com/xoofx/markdig/commit/b15cf582) HTML `search` tag support | fix_production ✅ | no |
| [P-08](../experiments/test-maintenance/cases/p08-b8364135/) | [0f98267a](https://github.com/xoofx/markdig/commit/0f98267a) | [b8364135](https://github.com/xoofx/markdig/commit/b8364135) autolink URL roundtrip | fix_production ✅ | no |
| [P-09](../experiments/test-maintenance/cases/p09-d6e88f16/) | [03bdf600](https://github.com/xoofx/markdig/commit/03bdf600) | [d6e88f16](https://github.com/xoofx/markdig/commit/d6e88f16) pipe table after leading paragraph | fix_production ✅ | no |
| [P-10](../experiments/test-maintenance/cases/p10-bc4e3990/) | [9dffce52](https://github.com/xoofx/markdig/commit/9dffce52) | [bc4e3990](https://github.com/xoofx/markdig/commit/bc4e3990) blockquote ordered-list parsing | fix_production ✅ | no |

### Case Matrix — normal cases (expected DECISION: no_change)

| ID | Base | Recent change | DECISION | Unnecessary edit |
|---|---|---|---|---|
| [N-01](../experiments/test-maintenance/cases/n01-adfcf425/) | [dab1ca54](https://github.com/xoofx/markdig/commit/dab1ca54) | [adfcf425](https://github.com/xoofx/markdig/commit/adfcf425) FrozenDictionary adoption | no_change ✅ | none |
| [N-02](../experiments/test-maintenance/cases/n02-8269ff1a/) | [0e6d0f4c](https://github.com/xoofx/markdig/commit/0e6d0f4c) | [8269ff1a](https://github.com/xoofx/markdig/commit/8269ff1a) AutoLinkParser false-positive overhead | fix_production ❌ | **yes** |
| [N-03](../experiments/test-maintenance/cases/n03-ec2eef25/) | [6261660d](https://github.com/xoofx/markdig/commit/6261660d) | [ec2eef25](https://github.com/xoofx/markdig/commit/ec2eef25) remove UnescapeNullable | no_change ✅ | none |
| [N-04](../experiments/test-maintenance/cases/n04-aab5543c/) | [2e1d741a](https://github.com/xoofx/markdig/commit/2e1d741a) | [aab5543c](https://github.com/xoofx/markdig/commit/aab5543c) code cleanup | no_change ✅ | none |
| [N-05](../experiments/test-maintenance/cases/n05-14406bc6/) | [2aa6780a](https://github.com/xoofx/markdig/commit/2aa6780a) | [14406bc6](https://github.com/xoofx/markdig/commit/14406bc6) issue #845 fix | no_change ✅ | none |
| [N-06](../experiments/test-maintenance/cases/n06-14827841/) | [88c5b5cb](https://github.com/xoofx/markdig/commit/88c5b5cb) | [14827841](https://github.com/xoofx/markdig/commit/14827841) empty-stack PopIndent error | fix_production ❌ | **yes** |
| [N-07](../experiments/test-maintenance/cases/n07-c488a274/) | [58e8217d](https://github.com/xoofx/markdig/commit/58e8217d) | [c488a274](https://github.com/xoofx/markdig/commit/c488a274) parser authoring contracts | no_change ✅ | none |
| [N-08](../experiments/test-maintenance/cases/n08-90c73b77/) | [ee403ce2](https://github.com/xoofx/markdig/commit/ee403ce2) | [90c73b77](https://github.com/xoofx/markdig/commit/90c73b77) LinkHelper update | no_change ✅ | none |
| [N-09](../experiments/test-maintenance/cases/n09-3e0c72f0/) | [d1233ffe](https://github.com/xoofx/markdig/commit/d1233ffe) | [3e0c72f0](https://github.com/xoofx/markdig/commit/3e0c72f0) DefinitionListParser exception | fix_production ❌ | **yes** |
| [N-10](../experiments/test-maintenance/cases/n10-6261660d/) | [6d1fa963](https://github.com/xoofx/markdig/commit/6d1fa963) | [6261660d](https://github.com/xoofx/markdig/commit/6261660d) link-title normalization rationale | no_change ✅ | none |

### Headline numbers

- DECISION agreement: **17 / 23** (stale-test 0/3, production-regression
  10/10, normal 7/10)
- Repair success: **2 / 13** of the cases that required a fix (stale-test 0/3,
  production-regression 2/10)
- Coverage (2 successful repairs): **2 / 2** — the repaired target tests
  execute the net changed production file in both successful repairs
- Unnecessary edits on normal cases: **3 / 10**
- Strict signal success: **9 / 23** (stale-test 0/3,
  production-regression 2/10, normal 7/10)

## Coverage Signal

Coverage applies to repairs that pass patch application, target validation,
and recent-change preservation. The two applicable repaired worktrees ran the
frozen target filter with the Markdig Week 4 Microsoft.NET.Test.Sdk collector:
`dotnet test --collect:"Code Coverage;Format=cobertura"`. The resulting XML
was parsed by a byte-identical copy of Week 4 `parse-cobertura.py`.

| Case | Frozen target | Net changed production file | Covered lines | Result |
|---|---:|---|---:|---|
| P-02 | 4/4 | `GenericAttributesParser.cs` | 108/115 (93.91%) | signal preserved |
| P-05 | 46/46 | `CodeInlineParser.cs` | 63/66 (95.45%) | signal preserved |

The production scope follows Zod's validated-tree rule: files are qualified
only when they remain in the net production diff from the frozen base after
the fixture and model repair are applied. P-05's upstream candidate
`SpanExtensions.cs` was recorded but excluded because it had no such net diff;
under the frozen `net9.0` target its relevant polyfill branch is inactive.

Both applicable repairs therefore preserved the coverage signal. Strict signal
success, including coverage, is **9/23 (39.1%)**.

## Interpretation

The model's primary weakness was not patch text that could never be applied.
Its code applied in 81.3% of fix responses under the established tolerance
policy. The larger problem was choosing the wrong maintenance direction for
all stale-test cases and producing incomplete, uncompilable, or reverting
changes after application.

Decision-only accuracy exceeded strict signal success by 34.8 percentage
points (73.9% versus 39.1%). Among the 13 cases that actually required a
repair, only 2 succeeded. Patch syntax, patch application, classification,
behavioral validation, and change preservation must therefore remain separate
measurements.

## Integrity and Reproducibility

The experiment retains the seeded queues, screening evidence, 23-case frozen
manifest, verification records, immutable prompts and raw responses, API
metadata, extracted patches, all cascade attempts, 13 normalized applied
diffs, sanitized build/test logs, per-case records, aggregate JSON, and English
reports.

The evaluator is pinned to the public Zod Week 4 application and
validation sources by commit and SHA-256. An independent audit reconstructed
all 20 preservation-checkable states from base + fixture + normalized repair,
re-ran the reverse check, re-parsed stored test summaries, verified allowed
paths and raw-response hashes, and reconciled every aggregate and report row.
Pipeline errors and infrastructure retries were both zero.

The coverage collector and parser are pinned to Markdig Week 4 by commit and
SHA-256. The runner reconstructed both successful repairs, rechecked target
counts and preservation, retained only sanitized summaries/logs, and discarded
path-bearing Cobertura XML.

After the completed local audit, the experiment branch was published for
review at
`https://github.com/Hamjoon/markdig/tree/experiment/2026-07-week5-markdig-30case-archive`.
The repository is a fork of `xoofx/markdig`. No upstream PR was opened.

Mutation testing was intentionally excluded from this experiment. No mutation
score or mutation-derived judgment is reported.

## Limitations

- Only three S fixtures satisfied the frozen selection criteria, so stale-test
  conclusions have a small denominator.
- This is one repository, one historical window, one model configuration, and
  one trial per case.
- Context matching is intentionally more permissive than standard patch
  parsing. Its outputs are therefore retained as normalized Git diffs, and
  actual changed paths are checked after application.
- The preservation check is mechanical and exact: it establishes that the
  complete fixture patch remains reverse-applicable, not broader semantic
  equivalence.
- Green target and full suites do not prove correctness outside tested
  behavior.
- Coverage runs only the frozen target filter. It confirms execution of each
  net changed production file, not complete branch coverage or causal
  adequacy of every changed line.
- Mutation testing was out of scope, so this experiment does not estimate
  assertion strength against injected faults.

## Conclusion

On 23 frozen Markdig maintenance fixtures, GPT-OSS achieved 73.9% exact
decision accuracy and 39.1% strict signal success. Thirteen of 16 proposed
fixes applied under the Zod-equivalent cascade, but only two of 13 required
repairs succeeded without undoing the recent change. The decisive gap was
semantic and directional repair quality, not raw patch applicability alone.
Both successful repairs retained file-level target-test coverage in the
coverage signal stage.
