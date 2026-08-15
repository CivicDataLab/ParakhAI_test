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
| `e2e-tests` | **paused** since 2026-08-11 (`if: false`) | By request, not due to failures. `test-summary`'s E2E-report steps are guarded on `needs.e2e-tests.result != 'skipped'` so the pipeline degrades cleanly on missing shard artifacts. To resume: delete the active `if: false` line and uncomment the real gated condition already sitting commented-out directly below it in `ci.yml` — do **not** restore `if: always()`, see the "Path-filtered CI" section below for why. |

`e2e-tests` now depends on `needs: [lint, load-tests, changes]` (as of the
2026-08-14 path-filtering change below) rather than just `visual-tests` —
resuming it still works independent of any of those, since the job's own
`if:` is what actually controls it.

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

The real in-CI test started failing within ~13 minutes. Reverted on report;
`api-tests` was cancelled at 20m29s (vs a 6m31s clean baseline — 3x+), and
`accessibility-tests` + `visual-tests` both actually completed *successfully*
despite running concurrently with it — the slowdown/failures were
concentrated in `api-tests`, not universal.

**Corrected 2026-08-12, after pulling the cancelled job's partial log**
(`gh api repos/.../actions/jobs/<id>/logs` — GitHub retains whatever a job
uploaded before it was killed): there IS a captured failure, and it's
diagnostic. `tests/api/test_audit_detail_api.py` — several tests sharing
fixture-heavy queries — failed together in sequence:

```
11:23:01Z RERUN
11:24:04Z RERUN   (~63s later)
11:25:05Z FAILED  (~61s later)
```

~60s between each attempt before it failed/retried is a timeout signature,
not an assertion bug — matches bug #3's fingerprint exactly (dev backend
overwhelmed under concurrent load), reproducing under Docker just as it did
under `runserver`. So: the Docker migration + #13/#14 fixes were NOT
sufficient to make this pairing safe. `accessibility-tests`/`visual-tests`
being fine is consistent with `api-tests`' fixture-heavy queries being the
specific concurrency-sensitive load, not the whole suite.

Also observed: because `visual-tests` only depends on `accessibility-tests`
(not `api-tests`), making accessibility fast + independent had a wider blast
radius than intended — `visual-tests` started overlapping with `api-tests`
too, not just accessibility. Any re-attempt should account for that
cascading effect, not just the two jobs whose `needs:` actually changed.

**Before re-attempting:** the failure signature is now known (timeout-driven
RERUN/RERUN/FAILED clusters on fixture-heavy `tests/api/test_audit_detail_api.py`
queries, ~60s per stalled attempt). A re-attempt should watch specifically for
recurrence of that exact pattern rather than treating a generic "it failed"
as sufficient — and should isolate whether it's `api-tests`' fixture load
specifically, since `accessibility-tests`/`visual-tests` showed no such
symptom running concurrently with it in this same run.

---

## Path-filtered CI (2026-08-14)

**Status: implemented, first path-filtering this repo has ever had.**

`ci.yml` previously ran the full chain — `api-tests` → `accessibility-tests`
→ `visual-tests` → `e2e-tests` — on every push/PR regardless of what changed.
A new `changes` job (`dorny/paths-filter@v3`) now detects which of six
categories (`api`, `accessibility`, `visual`, `performance`, `load`, `e2e`)
actually changed, and every suite job is gated on its own category. Two new
suites were added at the same time: `performance-tests` and `load-tests`
(previously performance only ran nightly via `scheduled.yml`; load didn't
run in any workflow at all).

Two categories from the original request were deliberately **not** turned
into their own jobs:

- **security** is a pytest *marker*, not a directory —
  `tests/api/test_security.py` carries `pytestmark = [pytest.mark.api,
  pytest.mark.security]`, so `api-tests`' existing `-m api` run already
  executes every security test. A dedicated job would just re-run a subset
  of `api-tests`.
- **data** (`tests/data/test_data.py`) has zero `def test_` functions — it's
  a shared `TestGraphQL`/`TestUsers`/etc. constants class. A `data-tests` job
  would collect 0 tests every run. `tests/data/**` changes instead route
  into the `api`, `e2e`, and `load` filters (the suites whose test files
  actually import `TestGraphQL`).

### Fail-open, not fail-closed

If the `changes` job errors, or is deliberately skipped via the
`workflow_dispatch` `run_all` input, every downstream job must still run —
a broken filter should never silently make every future PR pass CI having
run zero tests. Every gated job's condition includes:

```yaml
(needs.changes.result != 'success' || needs.changes.outputs.<category> == 'true')
```

`changes.result` is `'skipped'` under `run_all` (its own `if:` skips it) and
would be `'failure'` if the action itself errors — both `!= 'success'`, so
every category's clause is satisfied and every suite runs.

### The skip/failure-ambiguity gotcha (the reason `lint` is checked directly everywhere)

`needs.<job>.result == 'skipped'` is true for two completely different
reasons that are otherwise indistinguishable: (1) that job's own path filter
just didn't match — expected, fine — or (2) an *upstream* job genuinely
failed, e.g. `lint` breaks, which makes every job after it (whose `if:` now
includes `always()`) evaluate to `'skipped'` too, cascading the same value
down the whole chain. Checking only "did my immediate predecessor
succeed-or-skip" can't tell these apart.

The fix used throughout `ci.yml`: every gated job adds `lint` to its own
`needs:` and checks `needs.lint.result == 'success'` **directly**, not just
inferred transitively through its predecessor. `lint` is never path-filtered,
so its result is always unambiguous. This is why every gated job's `needs:`
list has three entries (`lint`, its immediate predecessor, `changes`) even
though `lint` isn't otherwise in that job's critical path — it's there
purely to make the direct reference legal.

**Verify this specifically, don't just trust the design**: intentionally
break `ruff` (e.g. commit an unused import) together with an unrelated
`tests/api/**` change, push, and confirm every downstream job shows
`skipped` — not that they ran anyway. If any of them run, the fail-open
logic has a real bug, not just a theoretical one.

### Why `always() && !cancelled()` reappears on accessibility-tests/visual-tests

These two jobs had **no** `if:` at all (relying on default `success()`
gating) since the 2026-08-12 fix documented above, specifically to avoid the
bare-`always()`-ignores-cancellation bug. Path filtering requires an
explicit `if:` again (a job needs custom logic to still be *evaluated* when
its predecessor was filtered-out-skipped rather than genuinely successful).
This is safe because it uses the same `always() && !cancelled()` pairing
already proven safe on `test-summary` — never bare `always()`. If you see
bare `always()` reappear on any suite job in this file, that is the
2026-08-12 bug coming back, not this change.
