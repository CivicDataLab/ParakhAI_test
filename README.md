# Parakh Test Framework

Production-ready Python + Playwright test automation framework for the **[Parakh AI Evaluation Platform](https://parakh.civicdataspace.in)** by CivicDataLab.

---

## Overview

| Layer | Tool | Coverage |
|---|---|---|
| E2E UI | Playwright + pytest | Auth, homepage, navigation, feature tabs, AI models, evaluations list + detail, New Evaluation wizard (draft, automated & manual modes, cancel paths), evaluators management, evaluator role, auditor flows, prompt libraries, mobile viewport |
| Accessibility | axe-playwright-python (WCAG 2.1 AA) | Axe scans, alt text, ARIA, keyboard, skip links, social-icon labels |
| Visual Regression | Pillow pixel-diff | Desktop / tablet / mobile viewports |
| API / HTTP | requests | Status codes, headers, response time, public and authenticated GraphQL contracts |
| Security | requests + Playwright | Cookie flags, browser storage, GraphQL auth/error handling, IDOR, CORS, and input sanitisation |
| Performance | CDP + Navigation Timing API | Load time, TTFB, LCP, mobile 3G, authenticated-route and resource-size budgets |
| Load | requests + concurrent workers | Concurrent GraphQL reads, draft creation, authentication, pagination, and UI degradation |

---

## Prerequisites

- **Python 3.11+**
- **pip** (or `pipx`)
- **Node.js 18+** (required by Playwright browser installer)
- Internet access to `dev.parakh.civicdataspace.in`

---

## Installation

```bash
# 1. Clone the repo
git clone <repo-url>
cd ParakhAI_test

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install Playwright browser binaries
playwright install --with-deps chromium

# 5. Configure environment
cp .env.example .env
# Fill in TEST_EMAIL_1, TEST_PASSWORD_1 at minimum
```

---

## Running Tests

### All tests
```bash
pytest
```

### By suite
```bash
pytest tests/e2e/           -m e2e           # E2E browser tests
pytest tests/accessibility/ -m accessibility  # WCAG / axe-core
pytest tests/visual/        -m visual         # screenshot regression
pytest tests/api/           -m api            # HTTP/API + security checks
pytest tests/performance/   -m performance    # load & timing metrics
pytest tests/load/          -m load           # explicit load/stress suite
```

### By marker
```bash
pytest -m smoke -v           # fast CI sanity subset
pytest -m auth -v            # authenticated tests only (needs TEST_EMAIL_1)
pytest -m mobile -v          # mobile-viewport tests (390px)
pytest -m regression_write   # write-side tests (needs SANDBOX_ORG_SLUG)
pytest -m security -v        # security checks; cookie checks also need TEST_EMAIL_1
pytest -m load -v            # load tests; mutation scenarios need SANDBOX_ORG_SLUG
```

Load tests are not intended for routine PR validation. Run them explicitly
against the dev/staging sandbox, not production. The complete unfiltered
`pytest` command includes them; use `pytest -m "not load"` for a normal local
full-suite run without stress scenarios.

### Single file / test
```bash
pytest tests/e2e/test_homepage.py -v
pytest tests/e2e/test_homepage.py::TestClass::test_name -v
```

### Parallel execution
```bash
pytest -n 2 tests/e2e/      # 2 workers (recommended for browser tests)
pytest -n auto tests/api/   # auto-detect workers (good for API tests)
```

### Sharded execution (mirrors CI)
```bash
pytest tests/e2e/ --splits 3 --group 1   # shard 1 of 3
pytest tests/e2e/ --splits 3 --group 2   # shard 2 of 3
pytest tests/e2e/ --splits 3 --group 3   # shard 3 of 3
```

### Debug with visible browser
```bash
HEADLESS=false SLOW_MO=500 pytest tests/e2e/ -v
```

### Against a different environment
```bash
BASE_URL=https://staging.parakh.civicdataspace.in pytest -m api -v
```

---

## Visual Regression Workflow

### Save baselines (first run)
```bash
pytest tests/visual/ -v
# Tests skip with "Baseline saved — re-run to compare"
```

### Compare against baselines
```bash
pytest tests/visual/ -v
# Tests fail if pixel diff > VISUAL_THRESHOLD (default 0.2%)
```

### Update a baseline after intentional UI change
```bash
rm snapshots/homepage_desktop_1440x900.png
pytest tests/visual/test_visual_regression.py::TestHomepageVisual::test_homepage_desktop_screenshot -v
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `BASE_URL` | `https://dev.parakh.civicdataspace.in` | Target platform URL |
| `GRAPHQL_URL` | `https://dev.api.parakh.civicdataspace.in/graphql/` | GraphQL endpoint |
| `ENVIRONMENT` | `development` | `local` / `development` / `staging` / `production` |
| `BROWSER` | `chromium` | `chromium` / `firefox` / `webkit` |
| `HEADLESS` | `true` | `false` to watch the browser |
| `SLOW_MO` | `0` | Milliseconds between each Playwright action |
| `TIMEOUT` | `30000` | Default Playwright timeout (ms) |
| `VIEWPORT_WIDTH` | `1440` | Browser viewport width (px) |
| `VIEWPORT_HEIGHT` | `900` | Browser viewport height (px) |
| `SCREENSHOT_ON_FAILURE` | `true` | Auto-screenshot on test failure |
| `VISUAL_THRESHOLD` | `0.2` | Max pixel-diff % for visual tests |
| `TEST_EMAIL_1` | — | Primary test account email |
| `TEST_PASSWORD_1` | — | Primary test account password |
| `TEST_EMAIL_2` | — | Secondary account for multi-user tests (`authenticated_page_u2`) |
| `TEST_PASSWORD_2` | — | Secondary account password |
| `TEST_USER_INDEX` | `1` | Active user slot — `1` or `2` |
| `SANDBOX_ORG_SLUG` | — | Org slug for write-side tests; unset = all `regression_write` tests skip |

---

## Test Markers Reference

| Marker | When to use |
|---|---|
| `@pytest.mark.e2e` | Browser UI end-to-end tests |
| `@pytest.mark.accessibility` | WCAG / axe-core tests |
| `@pytest.mark.visual` | Screenshot regression tests |
| `@pytest.mark.api` | HTTP/API tests; some security checks also inspect a browser session |
| `@pytest.mark.performance` | Page timing and resource-budget tests |
| `@pytest.mark.load` | Explicit load/stress tests, including concurrent reads and mutations |
| `@pytest.mark.security` | Security-focused HTTP and browser-session checks |
| `@pytest.mark.mobile` | Mobile-viewport tests (390×844) |
| `@pytest.mark.smoke` | Fast sanity subset for PR checks |
| `@pytest.mark.regression` | Full regression suite |
| `@pytest.mark.regression_write` | Mutating tests — auto-skip unless `SANDBOX_ORG_SLUG` is set |
| `@pytest.mark.auth` | Tests requiring an authenticated session (`TEST_EMAIL_1` must be set) |
| `@pytest.mark.skip_on_ci` | Tests excluded from CI environments |

---

## CI/CD Pipeline

```
Push / PR to main or dev
        │
        ▼
   ┌─────────┐
   │  lint   │  ruff check
   └────┬────┘
        │
   ┌────┴──────────────────────────────────────────┐
   │              (parallel jobs)                  │
   ├──────────┬──────────────────────┬─────────────┤
   │ api-tests│ e2e-tests (3 shards) │  a11y-tests │
   │          │  shard 1 | 2 | 3     │             │
   │          │  -n 2 per shard      │             │
   └──────────┴──────────────────────┴─────────────┘
              visual-tests (separate job)
                        │
              ┌─────────▼──────────┐
              │    test-summary    │
              │ downloads shards   │
              │ merge_test_reports │
              │ → GitHub Step      │
              │   Summary          │
              └────────────────────┘

Artifacts retained 30 days:
  e2e-shard-{1,2,3}        per-shard HTML + JSON reports + screenshots
  e2e-combined-report       merged JSON + Markdown summary
  api-test-report           API HTML report
  accessibility-report      axe JSON + HTML
  visual-regression-report  diff images + HTML
```

Triggers: `push` to `main` / `dev` / `develop`, `pull_request` to `main`, `workflow_dispatch`.

---

## Adding New Tests

1. **Choose the right folder**: `tests/e2e/`, `tests/api/`, etc.
2. **Name the file** `test_<feature>.py`
3. **Add the marker** at module level: `pytestmark = [pytest.mark.e2e]`
4. **Use Page Objects** from `pages/` — create a new one extending `BasePage` if needed, with selectors in a matching `locators/<feature>_locators.py`
5. **Run locally** before pushing:
   ```bash
   pytest tests/e2e/test_my_feature.py -v --reruns 0
   ```

### Page Object pattern
```python
# pages/my_feature_page.py
from pages.base_page import BasePage
from locators.my_feature_locators import MyFeatureLocators

class MyFeaturePage(BasePage):
    HEADING = MyFeatureLocators.HEADING

    def go_to_my_feature(self) -> "MyFeaturePage":
        self.navigate(self.config.url("/my-feature"))
        self.wait_for_load("domcontentloaded")
        self.wait_for_app_ready()
        self.skip_if_redirected_to_home("/my-feature")
        return self
```

### Test pattern
```python
# tests/e2e/test_my_feature.py
import pytest
from playwright.sync_api import Page
from pages.my_feature_page import MyFeaturePage

pytestmark = [pytest.mark.e2e, pytest.mark.regression, pytest.mark.auth]

def test_heading_visible(authenticated_page_fast: Page):
    page = MyFeaturePage(authenticated_page_fast)
    page.go_to_my_feature()
    assert page.is_visible(page.HEADING)
```

---

## Reports

After each run, reports are written to `reports/`:

| File | Contents |
|---|---|
| `reports/report.html` | Default HTML report (full run) |
| `reports/report.json` | pytest-json-report output |
| `reports/TEST_REPORT.md` | Markdown summary |
| `reports/e2e_report_shard_N.html` | Per-shard HTML (CI only) |
| `reports/e2e_shard_N.json` | Per-shard JSON (CI only) |
| `reports/e2e_combined.json` | Merged shard JSON (CI test-summary job) |
| `reports/e2e_summary.md` | Merged Markdown posted to GitHub Step Summary |
| `reports/a11y_report.html` | Accessibility HTML report |
| `reports/accessibility_report.json` | Structured axe violations JSON |
| `reports/accessibility_*_report.json` | Authenticated-route axe results |
| `reports/performance_metrics.json` | Public-page timing metrics |
| `reports/performance_metrics_auth.json` | Authenticated-route timing metrics |
| `reports/load_metrics.json` | Mutation, authentication, wizard, and UI load metrics |
| `reports/load_metrics_graphql.json` | Concurrent GraphQL read and pagination metrics |
| `screenshots/FAIL_*.png` | Failure screenshots |
| `screenshots/DIFF_*.png` | Visual regression diff images |

---

## Utility Scripts

All scripts share auth + GraphQL plumbing in `scripts/_api_client.py`: headless Playwright login through Keycloak using `TEST_EMAIL_1` / `TEST_PASSWORD_1`, access token from `/api/auth/session`, then GraphQL via `requests`. Defaults target the dev backend; override via `BASE_URL` / `GRAPHQL_URL`.

### `scripts/cleanup_drafts.py` — bulk-cancel DRAFT evaluations
```bash
python scripts/cleanup_drafts.py --dry-run
python scripts/cleanup_drafts.py
python scripts/cleanup_drafts.py --org-id 5
```

### `scripts/cleanup_all.py` — broader cleanup with age filter
```bash
python scripts/cleanup_all.py --dry-run
python scripts/cleanup_all.py --include-cancelled-older-than 7
python scripts/cleanup_all.py --status DRAFT,RUNNING
```

### `scripts/seed_test_data.py` — create N draft audits
```bash
python scripts/seed_test_data.py                        # 5 drafts in org 1
python scripts/seed_test_data.py --count 10
python scripts/seed_test_data.py --model-id 129
python scripts/seed_test_data.py --dry-run
```

### `scripts/sandbox_reset.py` — hard-reset the sandbox org
```bash
python scripts/sandbox_reset.py --dry-run
python scripts/sandbox_reset.py --yes      # non-interactive (CI)
```
Requires `SANDBOX_ORG_SLUG` in `.env` — refuses to run otherwise.

### `scripts/merge_test_reports.py` — merge CI shard reports
```bash
python scripts/merge_test_reports.py \
    reports/e2e_shard_1.json \
    reports/e2e_shard_2.json \
    reports/e2e_shard_3.json \
    --output reports/e2e_combined.json \
    --markdown reports/e2e_summary.md
```
Used by the `test-summary` CI job to unify per-shard results into a single Markdown summary posted to GitHub Step Summary.

---

## Sandbox org for write-side tests

Tests marked `@pytest.mark.regression_write` mutate platform state (creating evaluations, adding evaluators, etc.) and only run against a dedicated sandbox organisation. Set `SANDBOX_ORG_SLUG` in `.env` (or as a GitHub Actions secret) to enable them. The autouse `forbid_outside_sandbox` fixture in `tests/conftest.py` skips every `regression_write` test when it is unset.

---

## Project Structure

```
ParakhAI_test/
├── .github/workflows/
│   ├── ci.yml                   # PR + push pipeline (lint → parallel suites → summary)
│   └── scheduled.yml            # Nightly regression (02:00 UTC)
├── tests/
│   ├── e2e/                     # Browser UI tests (377 collected tests)
│   │   ├── test_auth.py
│   │   ├── test_homepage.py
│   │   ├── test_smoke_critical.py
│   │   ├── test_functional.py
│   │   ├── test_navigation.py
│   │   ├── test_feature_tabs.py
│   │   ├── test_models.py
│   │   ├── test_evaluations.py
│   │   ├── test_evaluation_detail.py
│   │   ├── test_regression_new_features.py
│   │   ├── test_new_evaluation_smoke.py
│   │   ├── test_new_evaluation_regression.py
│   │   ├── test_new_evaluation_full_flow.py
│   │   ├── test_new_evaluation_cancel.py
│   │   ├── test_evaluation_workspace.py
│   │   ├── test_evaluation_workspace_manual.py
│   │   ├── test_evaluators_management.py
│   │   ├── test_evaluators_management_write.py
│   │   ├── test_evaluator_role.py
│   │   ├── test_assignment_workflow.py
│   │   ├── test_multi_user_assignment.py
│   │   ├── test_auditor_evaluations.py
│   │   ├── test_auditor_model_detail.py
│   │   ├── test_ai_maker_dashboard.py
│   │   ├── test_org_selection.py
│   │   ├── test_prompt_libraries.py
│   │   ├── test_user_flows.py
│   │   └── test_mobile.py
│   ├── accessibility/           # Public + authenticated WCAG / axe-core tests
│   │   ├── test_accessibility.py
│   │   └── test_accessibility_auth.py
│   ├── visual/                  # Screenshot regression
│   ├── api/                     # HTTP-layer tests
│   │   ├── test_api.py
│   │   ├── test_graphql.py
│   │   ├── test_graphql_authenticated.py
│   │   └── test_security.py
│   ├── performance/             # Public/auth route timing + resource budgets
│   │   ├── test_performance.py
│   │   └── test_performance_auth.py
│   ├── load/                    # Concurrent API, auth, mutation, and UI load tests
│   │   ├── test_load.py
│   │   └── test_load_graphql.py
│   ├── data/
│   │   └── test_data.py         # GraphQL queries/mutations + sandbox constants
│   └── conftest.py              # All shared fixtures
├── pages/                       # Page Object Models
│   ├── base_page.py             # Base — all pages inherit from here
│   ├── home_page.py
│   ├── login_page.py
│   ├── dashboard_page.py
│   ├── ai_maker_page.py
│   ├── models_page.py
│   ├── evaluations_page.py
│   ├── evaluation_detail_page.py
│   ├── new_evaluation_page.py
│   ├── workspace_page.py
│   ├── evaluators_page.py
│   ├── evaluator_role_page.py
│   ├── auditor_model_detail_page.py
│   ├── org_selection_page.py
│   └── prompt_libraries_page.py
├── locators/                    # Raw CSS/text selectors (one file per page)
├── scripts/
│   ├── _api_client.py           # Shared auth + GraphQL helpers
│   ├── cleanup_drafts.py
│   ├── cleanup_all.py
│   ├── seed_test_data.py
│   ├── sandbox_reset.py
│   └── merge_test_reports.py   # Merges CI shard JSONs → combined report
├── utils/
│   ├── config.py
│   ├── helpers.py
│   ├── reporters.py
│   └── test_data_factory.py
├── docs/
│   ├── app_bugs.md              # Known platform bugs; all xfails link here
│   ├── a11y_findings.md
│   └── visual_diffs.md
├── snapshots/                   # Visual regression baselines
├── reports/                     # Generated reports (gitignored)
├── screenshots/                 # Failure + diff screenshots (gitignored)
├── pytest.ini
├── requirements.txt
├── .env.example
├── CLAUDE.md
├── CONTRIBUTING.md
├── SECURITY.md
└── README.md
```

---

## License

MIT — see `LICENSE` for details.
