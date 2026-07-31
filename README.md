# LLM-Based Test Maintenance on Real Markdig Commit History

This branch archives an experiment on automated test maintenance: after a real
repository change, can a language model decide whether to update stale tests,
fix production code, or leave a correct change alone, and then carry out the
required repair?

Cases were built from real commits in
[xoofx/markdig](https://github.com/xoofx/markdig). Each packet contains the
fixture, model prompt and response, patch evidence, validation output, and the
machine-readable verdict. The model was not told which of the three categories
the case belonged to.

## Reports

- [Summary report](./docs/markdig-v2-23case-report.md) — question, protocol, results, and observations
- [Full report](./docs/markdig-v2-23case-report-full.md) — execution details and all per-case results
- [Case selection record](./docs/markdig-23case-screening.md) — candidate mining and screening
- [Fixture verification record](./docs/markdig-23case-verification-results.md) — fresh reconstruction of all 23 fixtures
- [Evaluation protocol](./docs/markdig-23case-evaluation-protocol.md) — frozen decision, patch-application, preservation, and coverage rules

## Repository layout

- `docs/` — reports, protocols, and the chronological stage log
- `experiments/test-maintenance/` — case packets, three canonical aggregate JSON files, and pipeline helpers
- `experiments/test-maintenance/scripts/parse-cobertura.py` — byte-identical Markdig Week 4 coverage parser
- `experiments/test-maintenance/metadata/experiment.json` — compact candidate-selection and fixture-verification provenance
- `scripts/` — the three top-level entry points for mining, GPT-OSS execution, and Markdig signal evaluation

Each case lives under `experiments/test-maintenance/cases/<case>-<sha8>/`,
matching the case-centered layout used by the preceding Zod experiment.
Successful repair packets also contain a sanitized coverage summary
and execution log.

## Result snapshot

- Frozen fixtures: 23 (S=3, P=10, N=10)
- Exact decision: 17/23 (73.9%)
- Patch application: 13/16 (81.3%)
- Required repair success: 2/13 (15.4%)
- Strict signal success: 9/23 (39.1%)
- Coverage signal: 2/2 successful repairs preserved
- Pipeline errors and infrastructure retries: 0

The model under test was `openai/gpt-oss-120b`, one request per case at
temperature 0. Coverage used the Markdig Week 4 Test.Sdk collector and
`parse-cobertura.py` procedure. Mutation testing was excluded by instruction.

This is an orphan archive branch: it contains only the public experiment
package and does not inherit the Markdig source tree. The complete execution
history and the raw screening/verification logs remain on the
[`experiment/2026-07-week5-markdig-30case`](https://github.com/agent-eli/markdig/tree/experiment/2026-07-week5-markdig-30case)
branch. No pull request was opened against upstream Markdig.
