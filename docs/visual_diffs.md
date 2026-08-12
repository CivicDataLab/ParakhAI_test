# Visual Regression Diffs

Surfaced after each `pytest -m visual` run that produced `screenshots/DIFF_*.png` files. **Baselines are not auto-overwritten.** Each row needs human review — once you've decided "this is an intentional UI change", delete the corresponding `snapshots/<name>.png` and re-run the test to regenerate.

Format: append a new section per run. Don't delete old rows; mark them `resolved` once handled.

## Template

```
## Run YYYY-MM-DD HH:MM (env: dev|staging)

| diff file | baseline | suspected cause | decision | resolved |
|---|---|---|---|---|
| screenshots/DIFF_homepage_hero.png | snapshots/homepage_hero.png | hero copy changed in last release | accept new baseline | yes (regenerated 2026-05-08) |
| screenshots/DIFF_eval_list.png | snapshots/eval_list.png | unknown — pixel diff in row spacing only | needs review | no |
```

## Runs

### Run 2026-05-08 — Phase 4 first-pass baseline capture (env: dev)

First run on this branch. No prior baselines existed, so the suite operated in capture mode (each test saves its baseline and SKIPs with "Baseline saved — re-run to compare"). Subsequent runs will compare and produce DIFFs.

Result: 21 skipped (12 baselines saved + 9 missed), 0 fail.

**Baselines captured (12)** — all under `snapshots/`:

| target | file |
|---|---|
| homepage @ 1440×900 | `homepage_desktop_1440x900.png` |
| homepage @ 768×1024 | `homepage_tablet_768x1024.png` |
| homepage @ 390×844 | `homepage_mobile_390x844.png` |
| hero section | `hero_section_desktop.png` |
| footer | `footer_desktop.png` |
| dashboard role selector (auth) | `auth_dashboard_role_selector_desktop_1440x900.png` |
| org selector (auth) | `auth_org_selector_desktop_1440x900.png` |
| AI Maker dashboard (auth) | `auth_ai_maker_dashboard_desktop_1440x900.png` |
| auditor dashboard (auth) | `auth_auditor_dashboard_desktop_1440x900.png` |
| auditor assignments (auth) | `auth_auditor_assignments_desktop_1440x900.png` |
| auditor evaluations (auth) | `auth_auditor_evaluations_desktop_1440x900.png` |
| evaluation detail completed (auth) | `auth_evaluation_detail_completed_desktop_1440x900.png` |

**Baselines missing (5)** — `page.goto: Timeout 30000ms`:

| route | suspected cause |
|---|---|
| `/dashboard/ai-maker/1/ai-models` | bug #3 (dev env intermittent 4xx) |
| `/dashboard/ai-maker/1/evaluations` | bug #3 |
| `/dashboard/ai-maker/1/evaluations/new` | bug #3 + heavy SPA load |
| `/dashboard/ai-maker/1/auditors` | bug #3 |
| `/dashboard/ai-maker/1/prompt-libraries` | bug #3 |

Re-run `pytest -m visual` once dev is stable to capture these.

**Other skips (4) — homepage feature tabs:**

`test_feature_tabs_screenshot[chromium-{0..3}-tab_*]` reported "Tab index N not available — only 0 tabs found". The tab buttons exist on the homepage (verified via Playwright MCP earlier this session: "Automation-assisted Evaluation Environment" / "Expert-led Evaluations" / etc.), but the visual test's tab-locator doesn't match them. **Not a baseline gap; needs a test fix in `tests/visual/test_visual_regression.py`.** Filed as a follow-up — not in scope for first-pass baseline capture.

### Run 2026-05-08 — Phase 4 follow-up: tab fix + auth-route gap closed (env: dev)

Result: 9 newly captured baselines / 0 fail.

Two fixes landed:

1. **Feature-tabs locator rewrite** — homepage tabs render as plain `<button>`s (no `role="tab"`); old selector matched 0 elements. Refactored to anchor on the four known labels and capture the whole `<section>` per tab (covers active-button highlight + content panel). Test now parametrizes on `(tab_label, snapshot_label)` instead of index.
2. **`networkidle` → `load`** in `_capture_page_masked`. Auth-walled routes have background polling that prevents `networkidle` from settling — same workaround already in `HomePage.go_to_home`. Bumped post-load settle from 1.5s → 2.5s.

**Newly captured (9)** — under `snapshots/`:

| target | file |
|---|---|
| feature tab 0 (Automation-assisted) | `feature_tab_0_automation.png` |
| feature tab 1 (Expert-led) | `feature_tab_1_expert.png` |
| feature tab 2 (Sector-specific) | `feature_tab_2_sector.png` |
| feature tab 3 (Eval History) | `feature_tab_3_history.png` |
| AI Maker → models list | `auth_models_list_desktop_1440x900.png` |
| AI Maker → evaluations list | `auth_evaluations_list_desktop_1440x900.png` |
| AI Maker → new evaluation wizard | `auth_new_evaluation_wizard_desktop_1440x900.png` |
| AI Maker → auditors management | `auth_auditors_management_desktop_1440x900.png` |
| AI Maker → prompt libraries | `auth_prompt_libraries_desktop_1440x900.png` |

Baselines now total **21 / 21** for the visual suite. Phase 4 baseline capture is complete; subsequent runs will pixel-diff against these and surface DIFFs to review here.

### Run 2026-07-10 — Phase 7: re-run in fresh worktree, bug #15 filed (env: dev)

All 21 baselines present at run start (`snapshots/` is gitignored in this repo — the worktree doesn't get it from `git worktree add`; copied from the main checkout's local `snapshots/` dir, which matches this file's inventory exactly).

Result: **13 passed / 8 xfailed / 0 failed**, reproduced twice back-to-back. No baselines needed regenerating and no test-framework bugs were found — the suite is functioning as designed.

The 8 xfails are all under the pre-existing `VISUAL-002` classification (`_NON_DETERMINISTIC_VISUAL` in `tests/visual/test_visual_regression.py`, added in an earlier phase — see commit "Classify data-driven auth pages as non-deterministic visual (VISUAL-002)"). Four of them showed unusually large diffs (~43%), well beyond what "live stats / model dropdown ordering" would explain, so before accepting them as routine noise this run dug into the diff images and cross-checked against manual captures:

| diff file | baseline | diff % | investigation | decision |
|---|---|---|---|---|
| `screenshots/DIFF_auth_models_list_desktop_1440x900.png` | `snapshots/auth_models_list_desktop_1440x900.png` | 43.263% | Diff shows homepage hero/CTA/footer content bleeding through where the models-list page should be. Manual scripted repro (6 fresh authenticated loads) reproduced the same "homepage instead of dashboard page" failure in 1/6 trials. Baseline itself is correct (light theme, matches current UI when the bug doesn't fire). | **App bug, not baseline drift** — filed as bug #15 in `docs/app_bugs.md`. Left as `xfail`; baseline untouched. |
| `screenshots/DIFF_auth_new_evaluation_wizard_desktop_1440x900.png` | `snapshots/auth_new_evaluation_wizard_desktop_1440x900.png` | 43.107% | Same pattern — homepage content visible under the wizard's "Loading models…" panel. Reproduced twice on consecutive pytest re-runs of just this test. | Same as above — bug #15. No baseline change. |
| `screenshots/DIFF_auth_auditors_management_desktop_1440x900.png` | `snapshots/auth_auditors_management_desktop_1440x900.png` | 43.076% | Same pattern (Evaluators page chrome partially visible over homepage content). | Same as above — bug #15. No baseline change. |
| `screenshots/DIFF_auth_auditor_dashboard_desktop_1440x900.png` | `snapshots/auth_auditor_dashboard_desktop_1440x900.png` | 42.637% | Same pattern (auditor Home sidebar/avatar over homepage content). | Same as above — bug #15. No baseline change. |
| `screenshots/DIFF_auth_prompt_libraries_desktop_1440x900.png` | `snapshots/auth_prompt_libraries_desktop_1440x900.png` | 12.758% | Diff shows two stacked partial renderings (Prompt Libraries page chrome + homepage CTA/footer) — a mid-transition capture of the same underlying bug. Manual repro reproduced full homepage-fallback in 1/4 trials on this route. | Same root cause as bug #15 (lower diff % because the capture caught a partial/transitional state rather than a full homepage render). No baseline change. |
| `screenshots/DIFF_auth_evaluations_list_desktop_1440x900.png` | `snapshots/auth_evaluations_list_desktop_1440x900.png` | 0.887% | Small diff, localized to "Loading evaluations…" spinner vs. empty-state text — consistent with genuine live/async data timing, not the homepage-fallback bug (magnitude is 50x smaller than the bug #15 cases). | Genuine minor async noise — no action, `xfail` classification is correct as-is. |
| `screenshots/DIFF_auth_auditor_assignments_desktop_1440x900.png` | `snapshots/auth_auditor_assignments_desktop_1440x900.png` | 0.630% | Small diff, live assignment list ordering/count. | Genuine minor async noise — no action. |
| `screenshots/DIFF_auth_auditor_evaluations_desktop_1440x900.png` | `snapshots/auth_auditor_evaluations_desktop_1440x900.png` | 1.000% | Small diff, live evaluations list. | Genuine minor async noise — no action. |

**Follow-up worth doing (not done this run, flagged for review):** the `VISUAL-002` xfail reason string in `tests/visual/test_visual_regression.py` (~line 366) currently blames "model dropdown / live stats / variable list ordering" for all 8 routes — that's accurate for the 3 low-diff routes but understates what's happening on the 5 high-diff ones (see bug #15). Consider splitting the xfail message or diff-magnitude threshold so a ~43% diff (wrong page) is distinguishable in CI output from a ~1% diff (live data noise), since they currently read identically in the test summary.

Baselines remain **21 / 21**, unchanged this run.

### Run 2026-08-12 — Phase 11: baseline integrity audit (env: dev)

Not a diff-triage run. Audited what the committed baselines actually *contain*, after the suite reported "20 passed / 1 failed" while covering pages it had never captured.

**8 of the 12 authenticated baselines were invalid.** Full analysis in `docs/app_bugs.md` → Phase 11; inventory impact recorded here.

| baseline | what it actually contained | outcome |
|---|---|---|
| `auth_evaluation_detail_completed` | Next.js **404** — route `/evaluation/288` doesn't exist | route fixed; **no baseline yet** (see below) |
| `auth_ai_maker_dashboard` | stuck "Loading overview…" (bug #14) | regenerated clean — real stat cards, 6 model cards, populated Recent Evaluations |
| `auth_evaluations_list` | false-empty state | regenerated clean — 10 rows, "Page 1 of 31" |
| `auth_org_selector` | bare "Loading" spinner (bug #19 family) | regenerated clean |
| `auth_auditor_dashboard` | logged-out public homepage (bug #15) | **correctly refused** by the gate — #15 firing live |
| `auth_auditors_management` | logged-out public homepage (bug #15) | regenerated clean |
| `auth_models_list` | logged-out public homepage (bug #15) | regenerated clean |
| `auth_new_evaluation_wizard` | logged-out public homepage (bug #15) | regenerated clean |

The four homepage clones were found by checksum, not by eye — five files shared one md5 at exactly 348560 bytes, four of them auth routes. **Worth reusing as a technique:** byte-identical baselines across supposedly-different pages is a fast, zero-cost tell for this whole class of defect.

Also regenerated `auth_auditor_assignments` and `auth_auditor_evaluations` — these were valid, but carried the test account's name/initials and would have xfailed forever once identity masking landed. `auth_dashboard_role_selector` was regenerated separately: its 0.202% diff was a **legitimate frontend copy change** (commit `90f38dc` reworded both role cards — "For people building AI" → "Connect AI models to run evaluations", "For expert as evaluator" → "Evaluate AI Models you've been invited to review"). That one test was the only one in the suite doing its job, precisely because it was one of the few baselines showing a real page.

**Inventory: 21 → 20.** Missing is `auth_evaluation_detail_completed`; its route is now correct, but `completed_eval_id` found no audit meeting its `progress==100 AND totalTests>0 AND completedAt` bar and the UI-seeding fallback timed out — pre-existing fixture breakage, tracked separately, not a visual problem.

All baselines now have distinct md5s. Identity masking (header avatar + sidebar identity block) is active and was verified on a real capture *before* any regeneration — necessary ordering, since the four homepage clones were PII-free only by virtue of being logged out and would have *gained* PII on re-capture.
