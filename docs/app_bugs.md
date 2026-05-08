# App Bug Ledger

Bugs found by the test suite that are real product issues, not test flakes. Every `xfail` / `skip` in the test code that exists because of an app problem MUST reference a row here by `id`.

Format: append-only. When a bug is fixed in the app, mark `status: fixed` and the date — don't delete the row. Re-running the linked test should pass naturally; only then remove the `xfail`/`skip` from the test.

| id | area | summary | status | repro | related test(s) | first seen |
|---|---|---|---|---|---|---|
| 1 | wizard / draft | `Auto-saved` indicator never appears after editing the Evaluation Objective on `/evaluations/new`. URL stays without `auditId`. Draft is only persisted when the user clicks **Add Test Cases**. So either the auto-save feature is broken on dev, or the product copy/expectation needs to change. | open | Log in as `TEST_EMAIL_1` → AI Maker → CivicDataLab → New Evaluation → Start. On wizard, type into Evaluation Objective, blur, wait 10s. No `Auto-saved` / `Saving` text anywhere on page; URL has no `auditId`. Confirmed via Playwright MCP 2026-05-07. | `tests/e2e/test_new_evaluation_smoke.py::TestEvaluationConfigurationTab::test_filling_objective_triggers_auto_save_indicator` | 2026-05-07 |
| 2 | wizard / required-fields | The wizard's `Evaluation Scope` dropdown (`<select name="auditScope">`) is silently required: clicking **Add Test Cases** without selecting a scope succeeds visually (no error) but no draft is persisted (no `auditId` in URL). Either the field should be enforced with a visible validation error, or scope should default to "General". | open (test workaround landed) | In wizard, fill Objective + check a module + select Mode=Automated, but leave Scope as the placeholder. Click Add Test Cases. URL stays without `auditId`. With Scope=General, draft is created normally. Discovered via test framework + MCP 2026-05-07. | `tests/e2e/test_new_evaluation_smoke.py::TestAutomatedModeFlow::test_automated_mode_add_test_cases_shows_dataset_table`, `TestManualModeFlow::test_manual_mode_add_test_cases_shows_module_cards`, `TestDraftLifecycle::test_draft_appears_in_list_with_correct_badge_and_mode` | 2026-05-07 |
| 3 | dev-env stability | Dev frontend (`https://dev.parakh.civicdataspace.in`) intermittently returns HTTP 4xx mid-run; `home_page.py:46` guard fires `pytest.skip(...check VPN / IP allowlist...)`. Causes second-half of any smoke run to skip. Not a test bug — the env is unstable. Track separately from app bugs. | infra | Run `pytest -m smoke` for >5 minutes. Around midway, frontend returns 502/4xx for `BASE_URL`. Independent of caller IP — observed on multiple sessions. | All `e2e` + `smoke` tests transitively (skip cascade) | 2026-05-07 |

## Conventions

- One row per distinct bug. If two tests fail because of the same backend behaviour, list both in `related test(s)`.
- `repro` should be runnable from a fresh login — minimum steps that demonstrate the issue.
- `status` values: `open`, `in-progress`, `fixed` (with date), `wontfix` (with rationale).
- When you `xfail` a test for a bug here, use `pytest.xfail("App bug #N — see tasks/app_bugs.md")` so the link is greppable.
