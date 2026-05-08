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
