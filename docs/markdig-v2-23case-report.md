# GPT-OSS on Historical Test-Maintenance Fixtures in Markdig

- Subject project: [xoofx/markdig](https://github.com/xoofx/markdig) (a .NET/C# Markdown parser) / Model: `openai/gpt-oss-120b`
- Artifacts (per-case packets, prompts, model responses, logs, coverage results): [experiment/2026-07-week5-markdig-30case-archive](https://github.com/Hamjoon/markdig/tree/experiment/2026-07-week5-markdig-30case-archive) — the branch this report lives on

## Experiment question

When a code repository has just been changed and some tests now fail (or still
pass), the correct maintenance action depends on *why*: sometimes the tests are
outdated, sometimes the change introduced a bug, and sometimes nothing needs
fixing at all. This experiment asks whether a language model can tell these
situations apart and act correctly, given only the recent change and the
current test results. It repeats the question of the preceding Zod experiment
on a second repository and language (C# instead of TypeScript), under the same
protocol and judgment rules.

For 23 cases sampled from the commit history of the Markdig repository, the
model must:

1. Choose the correct response: `no_change` / `fix_tests` / `fix_production`.
2. Produce a successful repair — the target tests pass **and** the recent
   change is still present in the repaired code.
3. Keep the repaired tests covering the changed production code (coverage
   check).

## Case composition

Each case is built from a real pair of commits in the Markdig history: a base
version of the repository, plus one recent change applied on top of it. The
three categories differ in what that recent change is and what the correct
response is:

- **Stale-test cases** (3): the production behavior was changed intentionally,
  so tests written for the old behavior now fail. The tests are outdated, not
  the code — the correct response is `fix_tests`.
- **Production-regression cases** (10): a newly added test reveals a bug in
  the production code, so the test fails. The test is right and the code is
  wrong — the correct response is `fix_production`.
- **Normal cases** (10): the test suite still passes after the production
  change. Nothing is broken — the correct response is `no_change`.

Case IDs below are prefixed `S`, `P`, and `N` for the three categories
respectively, in acceptance order.

Cases were drawn by seeded random sampling from a candidate pool of Markdig
commits (2025-01 onward) filtered by pre-registered exclusion criteria. Each
candidate's failing/passing condition was verified by actually building and
running the tests, and verified candidates were accepted in queue order up to
ten per category. The stale-test category stopped at three: its complete
12-candidate queue was exhausted under the frozen criteria, and the window and
criteria were not expanded — the shortfall is retained as an observed result
(selection record:
[markdig-23case-verification-results.md](markdig-23case-verification-results.md);
screening record: [markdig-23case-screening.md](markdig-23case-screening.md)).

## Protocol overview

Every case runs under the same framing: with no category hint, the model
receives the recent-change diff, the test run output, and code snippets around
the change, then decides whether a modification is needed and, only if so,
produces a repair diff. Each case is a single request to the model — no
retries, no follow-up turns — with deterministic settings (temperature 0).
All 23 calls completed on the first attempt.

The prompt separates a **fixed template** from **per-case variables**. The
template — identical across all 23 cases — consists of the intro, the
constraint list (response protocol, no weakening or deleting of test
assertions, preserve nearby behavior that should still pass) and the required
response format (a `DECISION` first line, then a unified diff only if a fix is
chosen). The variables are the case's allowed-file list and three tagged
inputs: the recent-change diff, the test run output, and code snippets taken
±25 lines around the changed regions. Every prompt sent is archived per case.

Each returned fix is applied to the case fixture through the same tolerance
cascade as the Zod experiment (standard patch tools first, then a
context-matching applier), the project is rebuilt, the target and full test
suites are run, and a mechanical check verifies that the intended recent
change is still present in the repaired tree.

**Repair is judged as a single binary outcome:** *yes* means the target tests
pass **and** the recent change is still present in the repaired code; *no*
means anything else (the model's diff could not be applied, the build or tests
still fail, or the tests only pass because the repair undid the recent
change). The signal check measures test coverage of the changed production
file on successfully repaired code.

## Results

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

## Observations

- **The model never chose `fix_tests`, and errors flow in one direction.** It
  chose `fix_production` on all three stale-test cases and on three of the ten
  normal cases; the opposite errors (choosing `fix_tests` on a
  production-regression case) never occurred. As in the Zod experiment, the
  model treats the tests as the specification and doubts the recent production
  change — here the tendency is total: "the tests are outdated" was never
  selected as a direction.
- **Repairs that pass by undoing the change, and how they are caught.** The
  three unnecessary edits on normal cases all applied, built, and left the
  full test suite passing — yet each had reverted or altered the intended
  recent production change. Test results alone cannot distinguish these from
  harmless edits. The mechanical preservation check (verifying the recent
  change is still present in the repaired code) identified exactly these
  three, the same false-green pattern the Zod experiment observed.
- **Decision accuracy overstates end-to-end performance.** Exact decisions
  reached 17/23, but only 2 of the 13 fix-requiring cases produced a
  successful repair. Most applied fixes failed afterward — at build, at the
  test run, or at preservation — so patch syntax, patch application,
  classification, behavioral validation, and change preservation must be
  measured separately.

## Limitations

- Only three stale-test fixtures satisfied the frozen selection criteria, so
  stale-test conclusions rest on a small denominator.
- The prompt structure would allow the expected classification to be recovered
  from surface cues alone (where the diff is and whether tests fail), so
  DECISION agreement is an auxiliary metric.
- Coverage confirms the changed production file is executed by the repaired
  tests, but does not by itself measure how well those tests would detect
  future bugs. Mutation testing was out of scope by instruction.
- The preservation check is mechanical and exact: it establishes that the
  complete fixture patch remains reverse-applicable, not broader semantic
  equivalence.
- Single model (`gpt-oss-120b`), single repository (Markdig), one historical
  window, one trial per case.

---

Execution details and per-case records: [markdig-v2-23case-report-full.md](./markdig-v2-23case-report-full.md)
