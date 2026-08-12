# CI / GitHub Actions Notes

Durable findings about this repo's own CI workflows. Product defects belong in
[`app_bugs.md`](app_bugs.md); this file is for the pipeline itself — behaviours,
gotchas, and corrections to things we previously believed.

---

## Hyphenated job ids in `needs.<id>.result` are FINE (corrected 2026-08-12)

**Status: corrects a previously-held belief. No code change required.**

A note carried in our knowledge base claimed that `needs.<job-id>.result` "breaks
silently for hyphenated job ids (parses as subtraction)", and that jobs referenced
in expressions should therefore be renamed to avoid hyphens (e.g. `build-and-push`
→ `build`). Acting on that would have meant rewriting working guards in
`ci.yml` such as:

```yaml
if: needs.e2e-tests.result != 'skipped'
```

**That belief is wrong.** Hyphens are explicitly legal:

> "the property name must start with a letter or `_` and contain only alphanumeric
> characters, `-`, or `_`."
> — [GitHub Actions: contexts](https://docs.github.com/en/actions/reference/workflows-and-actions/contexts)

Verified independently with `actionlint` on a throwaway workflow: it resolves
`needs.e2e-tests.result` cleanly — typing the context as
`{e2e-tests: {outputs: {}; result: string}}` — while still rejecting a genuinely
undefined job id. That it rejects the undefined case proves it is doing real
resolution rather than waving everything through.

Reproduce in ~30 seconds:

```bash
# scratch workflow with a hyphenated job id referenced via needs.<id>.result
actionlint /path/to/scratch/.github/workflows/hyphen_test.yml
```

The original diagnosis was a misattribution. The symptom was real but the cause
was almost certainly one of the sibling gotchas from the same pipeline work:

- a job with `uses:` (reusable workflow call) **cannot** also declare `environment:`
  — GitHub rejects the whole file at parse time;
- a job with `if: always()` ignores workflow cancellation entirely and has no
  default timeout — always pair it with an explicit `timeout-minutes`.

**Still true and worth keeping:** `failure()` / `success()` builtins are a fine
choice for gating a job after a `workflow_call` job — just not for the hyphen
reason.

### Real caveat that does hold

Dereferencing a genuinely nonexistent property yields an **empty string**, silently.
So a typo'd `needs` reference fails **open** — a guarded step runs when you expected
it to be skipped — rather than failing loudly. Worth a second look whenever a guard
"doesn't seem to be doing anything".

### Takeaway

A recorded lesson is evidence, not proof — especially a "X breaks silently" claim,
which is exactly the shape that gets misattributed (real symptom, wrong assigned
cause). Verify against primary docs or a linter before letting one change working
code or contort a naming scheme.

---

## Currently paused jobs

| Job | Status | Notes |
|---|---|---|
| `e2e-tests` | **paused** since 2026-08-11 (`if: false`) | By request, not due to failures. `test-summary`'s E2E-report steps are guarded on `needs.e2e-tests.result != 'skipped'` so the pipeline degrades cleanly on missing shard artifacts. To resume, delete the `if: false` line to restore `if: always()`; the guards are harmless and can stay. |

Note the chain `e2e-tests needs: visual-tests` — resuming `e2e-tests` alone works
regardless of `visual-tests`, since the job's own `if:` controls it.

---

## Tried making api-tests + accessibility-tests concurrent — reverted same day (2026-08-12)

**Status: reverted. `ci.yml` is back to the full serial chain.**

Theory going in: bug #3's root cause (dev backend overwhelmed under concurrent
load, producing "too many clients"/ReadTimeouts) might no longer apply, since
two things changed the same day — the backend moved from `runserver` to a
Docker deployment, and bugs #13/#14 (routes that used to hang indefinitely)
were independently re-verified fixed (both now resolve in under 30s).

Changed `accessibility-tests` from `needs: api-tests` to `needs: lint`, so it
would start alongside `api-tests` instead of after it. A local 2-suite
concurrency smoke test beforehand showed no pool-exhaustion symptoms — but
was confounded by an unrelated CI run hitting the same backend at the same
time (this branch has an open PR into `main`, so every push auto-triggers a
run), so it wasn't treated as conclusive on its own.

The real in-CI test started failing within ~13 minutes. Reverted immediately
on report; the run was cancelled rather than left to finish, so there is
**no captured job log of the actual failure mode** — that's the gap to close
before trying again, not a reason to assume the theory was wrong. Also
observed: because `visual-tests` only depends on `accessibility-tests` (not
`api-tests`), making accessibility fast + independent had a wider blast
radius than intended — `visual-tests` started overlapping with `api-tests`
too, not just accessibility. Any re-attempt should account for that
cascading effect, not just the two jobs whose `needs:` actually changed.

**Before re-attempting:** get a completed (not cancelled) run's job logs
first, so the failure signature can actually be diagnosed — same-shape
ReadTimeouts as bug #3, or something new post-Docker-migration.
