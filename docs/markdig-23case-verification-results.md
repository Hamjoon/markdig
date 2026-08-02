# Markdig Week 5 Fixture Verification Report

## Result

**PASS — 23 of 23 accepted fixtures reproduced from fresh worktrees.**

For every accepted case, the verifier reconstructed the state through the
frozen screening procedure, rebuilt the relevant Markdig test project, reran
the required target or full-suite tests, and compared the fresh record with
the original screening record.

- Reverified cases: 23
- Reverified counts: S=3, P=10, N=10
- Accepted again: 23
- Exact test-count matches: 23
- Exact fixture-identity matches: 23
- Pipeline errors: 0
- Remaining worktrees after verification: 0

The aggregate fresh-worktree record is archived under
`fixture_verification` in
`experiments/test-maintenance/metadata/experiment.json`. The metadata bundle's
SHA-256 is
`fc09a2b8bad969c05cd74fade4a2078e98e6189cbd75c8d1d1e8ddaff4fb5855`.
Public model and validation evidence is grouped under
`experiments/test-maintenance/cases/`; the full execution branch retains the
original per-command verification logs.

## Fresh Executable Evidence

Counts use `F/P/S/T` for failed/passed/skipped/total.

| Case | Fresh executable evidence | Exact count match | Identity match |
|---|---|---:|---:|
| S-01 | base target 0F/90P/0S/90T → stale target 7F/83P/0S/90T | yes | yes |
| S-02 | base target 0F/74P/0S/74T → stale target 1F/73P/0S/74T | yes | yes |
| S-03 | base target 0F/65P/0S/65T → stale target 2F/63P/0S/65T | yes | yes |
| P-01 | oracle target 2F/13P/0S/15T → full target 0F/15P/0S/15T; full suite 0F/3542P/1S/3543T | yes | yes |
| P-02 | oracle target 1F/3P/0S/4T → full target 0F/4P/0S/4T; full suite 0F/3551P/1S/3552T | yes | yes |
| P-03 | oracle target 3F/104P/0S/107T → full target 0F/107P/0S/107T; full suite 0F/3774P/1S/3775T | yes | yes |
| P-04 | oracle target 1F/124P/0S/125T → full target 0F/125P/0S/125T; full suite 0F/3540P/1S/3541T | yes | yes |
| P-05 | oracle target 1F/45P/0S/46T → full target 0F/46P/0S/46T; full suite 0F/3552P/1S/3553T | yes | yes |
| P-06 | oracle target 1F/22P/0S/23T → full target 0F/23P/0S/23T; full suite 0F/3775P/1S/3776T | yes | yes |
| P-07 | oracle target 1F/61P/0S/62T → full target 0F/62P/0S/62T; full suite 0F/3532P/1S/3533T | yes | yes |
| P-08 | oracle target 3F/9P/0S/12T → full target 0F/12P/0S/12T; full suite 0F/3778P/1S/3779T | yes | yes |
| P-09 | oracle target 2F/58P/0S/60T → full target 0F/60P/0S/60T; full suite 0F/3558P/1S/3559T | yes | yes |
| P-10 | oracle target 1F/50P/0S/51T → full target 0F/51P/0S/51T; full suite 0F/3782P/1S/3783T | yes | yes |
| N-01 | base suite 0F/3453P/1S/3454T → changed suite 0F/3453P/1S/3454T | yes | yes |
| N-02 | base suite 0F/3468P/1S/3469T → changed suite 0F/3468P/1S/3469T | yes | yes |
| N-03 | base suite 0F/3539P/1S/3540T → changed suite 0F/3539P/1S/3540T | yes | yes |
| N-04 | base suite 0F/3541P/1S/3542T → changed suite 0F/3541P/1S/3542T | yes | yes |
| N-05 | base suite 0F/3543P/1S/3544T → changed suite 0F/3543P/1S/3544T | yes | yes |
| N-06 | base suite 0F/3444P/1S/3445T → changed suite 0F/3444P/1S/3445T | yes | yes |
| N-07 | base suite 0F/3606P/1S/3607T → changed suite 0F/3606P/1S/3607T | yes | yes |
| N-08 | base suite 0F/3453P/1S/3454T → changed suite 0F/3453P/1S/3454T | yes | yes |
| N-09 | base suite 0F/3444P/1S/3445T → changed suite 0F/3444P/1S/3445T | yes | yes |
| N-10 | base suite 0F/3539P/1S/3540T → changed suite 0F/3539P/1S/3540T | yes | yes |

## Integrity Checks

All checks passed:

- Category result arrays match their complete queue order and SHA values.
- Each accepted result agrees with its screening record.
- Every required build succeeded.
- S base targets are green and stale targets are red.
- P oracle targets are red; full targets and full suites are green.
- N base and production-changed full suites are green and non-empty.
- All 23 accepted candidate SHAs are unique and outside the smoke set.
- Construction paths match the queue metadata; no generated C# file entered
  an apply set.
- All JSON files parse.
- Stored logs contain no local absolute path, username, hostname, or project
  workspace identifier.
- Verification left no detached worktree or build product in the repository.

## Freeze Boundary

This verification freezes the fixture inputs and executable expectations. It
does not contain a model response, repair attempt, or later change to a
candidate, queue, category, or acceptance rule.
