# Markdig Week 5 GPT-OSS Model-Run Protocol

## Gate Scope

This gate performs exactly one model-under-test call for each of the 23 frozen
fixtures. It captures immutable inputs, the raw assistant response, API usage,
and transport metadata. It does not apply a returned patch, run repaired
tests, score a decision, analyze outcomes, or write the final experiment
report.

The frozen fixture source is commit
`887caeb67bfe637030d625dc455aaaca9584bb5a`, with manifest counts S=3,
P=10, N=10.

## Model and Sampling

- Provider: OpenRouter chat completions API
- Model: `openai/gpt-oss-120b`
- Temperature: `0`
- Conversation: one user message, one assistant response
- Order: `cases.json` order, S then P then N
- Primary trials: exactly 23, one per frozen fixture

An HTTP/transport failure that produces no assistant response may be retried
with exponential backoff. A response is never retried because its decision,
format, or diff is poor; that would change the experimental observation.

## Prompt Contract

Every case uses the same English template. The prompt contains:

1. The path-restricted recent-change diff used to construct the fixture.
2. The frozen targeted/full-suite test output from fixture verification.
3. Bounded snippets around the changed test and production hunks, read from
   the exact revision represented by the fixture state.
4. The allowed test and production paths.

The prompt does not expose the case ID, category label, or expected decision.
It requires the first response line to be exactly one of:

- `DECISION: no_change`
- `DECISION: fix_tests`
- `DECISION: fix_production`

For a change decision, the response must then contain a unified diff. For
`no_change`, it must contain no diff. The model is instructed not to weaken,
delete, or skip assertions and to preserve nearby behavior.

## Fixture-Specific Input Construction

- S: production diff applied to base production and base tests; failing
  stale-target output; base-revision test snippets and upstream-revision
  production snippets.
- P: upstream test/spec diff applied to base production; failing
  oracle-target output; upstream-revision test/spec snippets and base-revision
  production snippets.
- N: production diff applied to base with a green full suite; no test snippet;
  upstream-revision production snippets.

Generated C# files are never included in an allowed path, fixture patch, or
snippet source.

## Stored Evidence

Preparation writes, per case:

- `fixture.patch`
- `test-output.txt`
- `prompt.md`
- `input.json` with SHA-256 digests and revision/path metadata

The API run adds:

- `gptoss-response.md`
- `gptoss-usage.json`
- `gptoss-run.json`

The OpenRouter credential is supplied only through the process environment.
It is never written to a prompt, command artifact, log, or repository file.

## Stop Condition

After all 23 response bundles pass structural completeness and secret/path
scans, commit the raw run artifacts locally, report the gate result, and stop.
Any repair validation, outcome scoring, or report audit requires a separate
approval.
