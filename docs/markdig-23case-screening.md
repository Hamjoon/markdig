# Markdig Week 5 Fixture Screening Report

## Status

Candidate mining and executable screening are complete. The frozen fixture
set contains **23 cases: S=3, P=10, N=10**. The pre-registered target was up
to ten cases per category, but the protocol required queue exhaustion rather
than expanding the history window or relaxing an executable condition.

This report covers fixture selection only. No model-under-test run was
performed during mining, screening, or fixture freeze.

## Frozen Inputs

- Repository history endpoint: `fc705234fa211d179ee1d5e7656b51ab99f70ca9`
- History window start: 2025-01-01
- Pre-registration commit: `4c2a0fdab1d8ec95d6f7270b4bf49c8002aac92f`
- Completed screening artifacts: `771692a0b53d411661a3a8729ce630c9635214a8`
- Seed: `20260731`
- Canonical queue digest: `0578d21953459aa81684a5470c59d15a0574c712d0066812bfa91d70251a0c4d`
- `experiments/test-maintenance/screening_queues.json` file SHA-256:
  `34955ee9afcc419fb5626206ca640af3a8c8a33b6ed34880f91164785bb1428a`

## Mining and Screening Outcome

| Category | Pool | Screened | Accepted | Rejected | Not screened after quota |
|---|---:|---:|---:|---:|---:|
| S | 12 | 12 | 3 | 9 | 0 |
| P | 23 | 17 | 10 | 7 | 6 |
| N | 32 | 10 | 10 | 0 | 22 |
| **Total** | **67** | **39** | **23** | **16** | **28** |

Rejection taxonomy:

- S: `stale-state-green` ×7, `base-suite-red` ×1,
  `stale-state-build-failure` ×1.
- P: `test-oracle-uncompilable` ×6, `test-oracle-green` ×1.
- N: no rejection before the ten-case quota was reached.

There were no pipeline errors or screening retries. The S shortfall is an
experimental result: all twelve S candidates were screened, and only three
satisfied the pre-registered executable stale-test condition.

## Accepted Fixture Set

| Case | Category | Upstream | Base | Subject |
|---|---|---|---|---|
| S-05 | S | `12590e5fbe17` | `8c01cf054971` | feat(link-helper): improve ASCII normalization handling (#911) |
| S-07 | S | `5365879a23c9` | `a9bd7c6a5e1a` | Fix AbbreviationExtension corrupting emphasis/bold/italic resolution (#935) (#936) |
| S-09 | S | `148fd08b1d56` | `c488a2749719` | Add span validation/update APIs and tests |
| P-04 | P | `d548b82bcd26` | `7ff8db901659` | Add support for a table without an extra new line before it |
| P-06 | P | `781d9b536598` | `543570224e94` | Remove leading newline in block attributes (#896) |
| P-07 | P | `fcbf8170633e` | `5dca4149a518` | Fix CJK emphasis after HTML entity newlines (#941) |
| P-08 | P | `5a3c20607662` | `682c727288de` | Fixes #878: render indent and 0 blocks |
| P-09 | P | `800235ba7ab7` | `d5f8a809a00d` | Fix IndexOutOfRangeException in CodeInlineParser (#900) |
| P-11 | P | `0f98267a8519` | `fcbf8170633e` | Fix pipe table cells with unmatched subscript (#932) |
| P-14 | P | `b15cf582a538` | `61e9be290b1d` | Add 'search' HTML tag support |
| P-15 | P | `b83641351f67` | `0f98267a8519` | Fix roundtrip autolink URLs (#919) |
| P-16 | P | `d6e88f16f7d2` | `03bdf6008631` | Fix pipe table parsing with a leading paragraph (#905) |
| P-17 | P | `bc4e399087e1` | `9dffce52b610` | Fix blockquote ordered list parsing (#887) |
| N-01 | N | `adfcf4252964` | `dab1ca548373` | Use FrozenDictionary in a couple places |
| N-02 | N | `8269ff1af544` | `0e6d0f4cb24c` | Improve AutoLinkParser overhead for false-positive opening chars |
| N-03 | N | `ec2eef25b2a7` | `6261660d377e` | Remove HtmlHelper.UnescapeNullable |
| N-04 | N | `aab5543cb5b3` | `2e1d741aaf15` | Code cleanup |
| N-05 | N | `14406bc60d51` | `2aa6780a3071` | Fixes issue #845 |
| N-06 | N | `148278417f5a` | `88c5b5cb410f` | Added error throwing when stack is empty and PopIndent() is called |
| N-07 | N | `c488a2749719` | `58e8217ddb0d` | Document parser authoring contracts and migration risks |
| N-08 | N | `90c73b775453` | `ee403ce28f1a` | Update src/Markdig/Helpers/LinkHelper.cs |
| N-09 | N | `3e0c72f0430c` | `d1233ffe66da` | Fixes exception in DefinitionListParser.GetCurrentDefinitionList() |
| N-10 | N | `6261660d377e` | `6d1fa96389c8` | Explain why not to normalize link title into empty strings |

The machine-readable source of truth is
`experiments/test-maintenance/cases.json`, whose SHA-256 is
`3b572f56a22b141a1387a15447598d1fc013ad1628b7ae355e27147318a382a1`.
The complete mining, screening, and fresh fixture-verification records are
grouped in `experiments/test-maintenance/metadata/experiment.json`.

## Freeze Decision

The 23 accepted candidate SHAs are unique across categories, none is one of
the three excluded week-4 smoke candidate SHAs, and every fixture is
reconstructable from its recorded base SHA plus path-restricted upstream
diffs. No generated C# file is included in an apply set.

The fixture count is therefore frozen at **23**, with the S=3 shortfall
retained as observed evidence rather than repaired by post-selection changes.
