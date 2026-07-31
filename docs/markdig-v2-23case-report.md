# GPT-OSS on Historical Test-Maintenance Fixtures in Markdig

## Executive Summary

This Week 5 experiment tested whether `openai/gpt-oss-120b` could distinguish
three maintenance situations in Markdig and return a successful action:

- stale tests that should be updated (S),
- production regressions exposed by new tests (P), and
- already-correct changes requiring no action (N).

The frozen dataset contained 23 cases: S=3, P=10, N=10. GPT-OSS made the exact
decision in **17/23 cases (73.9%)**. Under the same patch-application and
recent-change-preservation procedure used in Zod Week 4, strict signal success
was **9/23 (39.1%)**: two successful P repairs and seven correct N no-change
actions.

The model diffs were not standard-format, so the Zod-style context matcher was
needed. It applied 13/16 without editing model code. The central result is
therefore not “no executable patches.” It is that context-applicable code was
common, while successful required repair was rare: **2/13 required repairs
(15.4%)**.

## Research Question

Given a recent change diff, current test output, bounded relevant code
snippets, and an allowed-file list, can GPT-OSS:

1. choose `fix_tests`, `fix_production`, or `no_change` correctly;
2. produce an allowed repair that applies under the established Zod cascade;
3. restore the required tests without undoing the intended recent change?

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

## Corrected Evaluation Procedure

An initial evaluation incorrectly stopped on model diff formatting before
trying the established application cascade. That was stricter than the Zod
Week 4 procedure and made the reported 0/16 application result non-comparable.
The corrected evaluation reused the immutable responses and applied this fixed
cascade from an identical committed fixture state before each attempt:

1. ordinary `git apply`;
2. `git apply --recount`;
3. GNU/BSD `patch` with fuzz 3;
4. the Zod context matcher, which locates unchanged pre-images and tolerates
   bare or inaccurate hunk coordinates.

After a successful application, Git derived and enforced the actual allowed
paths. The project was rebuilt; S/P target tests and the full suite were run;
then `git apply --reverse --check fixture.patch` verified that the intended
recent change remained present. No model response was changed or regenerated.

## Results

| Metric | Overall | S | P | N |
|---|---:|---:|---:|---:|
| Exact decision | 17/23 (73.9%) | 0/3 | 10/10 | 7/10 |
| Response-shape contract | 23/23 (100.0%) | 3/3 | 10/10 | 10/10 |
| Patch applied | 13/16 (81.3%) | 2/3 | 8/10 | 3/3 fix responses |
| Required repair success | 2/13 (15.4%) | 0/3 | 2/10 | not applicable |
| Strict signal success | 9/23 (39.1%) | 0/3 | 2/10 | 7/10 |

Decision confusion was unchanged:

- all 3 S cases were predicted `fix_production`, not `fix_tests`;
- all 10 P cases were predicted `fix_production` correctly;
- 7 N cases were predicted `no_change` correctly;
- 3 N cases were predicted `fix_production` incorrectly;
- `fix_tests` was never selected.

The Zod cascade attempted all 16 fixes and applied 13 through context matching.
Three patches (S-05, P-08, P-14) matched no frozen candidate pre-image.

P-06 and P-09 were the two successful required repairs. Both changed only the
allowed production file, preserved the recent test-oracle change, passed their
non-empty target tests, and passed the full suite. Of the other applied P
patches, five built but left target/full failures and one failed to build.

The three false-positive N fixes applied and left the full suite green, but all
three failed recent-change preservation by reversing the intended normal
production change. A test-only green judgment would have incorrectly counted
them as acceptable actions.

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

The corrected evaluator is pinned to the public Zod Week 4 application and
validation sources by commit and SHA-256. An independent audit reconstructed
all 20 preservation-checkable states from base + fixture + normalized repair,
re-ran the reverse check, re-parsed stored test summaries, verified allowed
paths and raw-response hashes, and reconciled every aggregate and report row.
Pipeline errors and infrastructure retries were both zero.

After the completed local audit, the experiment branch was published for
review at
`https://github.com/agent-eli/markdig/tree/experiment/2026-07-week5-markdig-30case-archive`.
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
- Mutation testing was out of scope, so this experiment does not estimate
  assertion strength against injected faults.

## Conclusion

On 23 frozen Markdig maintenance fixtures, GPT-OSS achieved 73.9% exact
decision accuracy and 39.1% strict signal success. Thirteen of 16 proposed
fixes applied under the Zod-equivalent cascade, but only two of 13 required
repairs succeeded without undoing the recent change. The decisive gap was
semantic and directional repair quality, not raw patch applicability alone.
