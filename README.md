# Parakh Test Framework

Production-ready Python + Playwright test automation framework for the **[Parakh AI Evaluation Platform](https://parakh.civicdataspace.in)** by CivicDataLab.

---

## Overview

| Layer | Tool | Coverage |
|---|---|---|
| E2E UI | Playwright + pytest | Homepage, navigation, auth, feature tabs, AI models, evaluations list, New Evaluation wizard (Draft & Auto-Save — Automated and Manual modes) |
| Accessibility | axe-playwright-python (WCAG 2.1 AA) | Axe scans, alt text, ARIA, keyboard |
| Visual Regression | Pillow pixel-diff | Desktop / tablet / mobile viewports |
| API / HTTP | requests | Status codes, headers, response time |
| Performance | CDP + Navigation Timing API | Load time, TTFB, LCP, mobile 3G |

---

## Prerequisites

- **Python 3.11+**
- **pip** (or `pipx`)
- **Node.js 18+** (required by Playwright browser installer)
- Internet access to `parakh.civicdataspace.in`

---

## Installation

```bash
# 1. Clone the repo
git clone <repo-url>
cd parakh-test-framework

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install Playwright browser binaries
playwright install --with-deps chromium

# 5. Configure environment (optional — defaults point to production)
cp .env.example .env
# Edit .env as needed
```

---

## Running Tests

### Run all tests
```bash
pytest
```

### Run a specific suite
```bash
pytest tests/e2e/          -m e2e           # E2E only
pytest tests/accessibility/ -m accessibility  # Accessibility only
pytest tests/visual/        -m visual         # Visual regression only
pytest tests/api/           -m api            # API tests only (no browser)
pytest tests/performance/   -m performance    # Performance tests only
```

### Run a single test file
```bash
pytest tests/e2e/test_homepage.py -v
```

### Run a single test by name
```bash
pytest tests/e2e/test_homepage.py::TestHomepageLoads::test_homepage_loads_successfully -v
```

### Run smoke tests (fast CI subset)
```bash
pytest -m smoke -v
```

### Run authenticated tests only
```bash
# Requires TEST_EMAIL_1 and TEST_PASSWORD_1 to be set in .env
pytest -m auth -v
```

### Run New Evaluation smoke / regression tests
```bash
pytest tests/e2e/test_new_evaluation_smoke.py -v       # smoke (9 tests)
pytest tests/e2e/test_new_evaluation_regression.py -v  # regression (12 tests)
```

### Run in parallel (8 workers)
```bash
pytest -n 8 -m "api or e2e"
```

### Run with visible browser (debugging)
```bash
HEADLESS=false SLOW_MO=500 pytest tests/e2e/ -v
```

### Run against a different environment
```bash
BASE_URL=https://staging.parakh.civicdataspace.in pytest tests/api/ -v
```

---

## Visual Regression Workflow

### First run — save baselines
```bash
pytest tests/visual/ -v
# Tests will SKIP with "Baseline saved — re-run to compare"
```

### Subsequent runs — compare against baselines
```bash
pytest tests/visual/ -v
# Tests will FAIL if pixel diff > VISUAL_THRESHOLD (default 0.1%)
```

### Update baselines after intentional UI changes
```bash
# Delete the specific snapshot(s) you want to update
rm snapshots/homepage_desktop_1440x900.png

# Re-run to save the new baseline
pytest tests/visual/test_visual_regression.py::TestHomepageVisual::test_homepage_desktop_screenshot -v
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `BASE_URL` | `https://parakh.civicdataspace.in` | Target platform URL |
| `ENVIRONMENT` | `production` | `local` / `staging` / `production` |
| `KEYCLOAK_URL` | _(same origin)_ | SSO provider URL if on a different domain |
| `BROWSER` | `chromium` | `chromium` / `firefox` / `webkit` |
| `HEADLESS` | `true` | `false` to watch the browser |
| `SLOW_MO` | `0` | Milliseconds between each action |
| `TIMEOUT` | `30000` | Default Playwright timeout (ms) |
| `VIEWPORT_WIDTH` | `1440` | Browser viewport width (px) |
| `VIEWPORT_HEIGHT` | `900` | Browser viewport height (px) |
| `SCREENSHOT_ON_FAILURE` | `true` | Auto-screenshot on failure |
| `VISUAL_THRESHOLD` | `0.1` | Max pixel-diff % for visual tests |
| `TEST_EMAIL_1` | — | Primary test account email (`authenticated_page`) |
| `TEST_PASSWORD_1` | — | Primary test account password |
| `TEST_EMAIL_2` | — | Secondary test account email (`authenticated_page_u2`) |
| `TEST_PASSWORD_2` | — | Secondary test account password |
| `TEST_USER_INDEX` | `1` | Active user slot — `1` or `2` |
| `RETRY_COUNT` | `2` | Number of automatic retries for flaky tests |
| `RETRY_DELAY` | `2.0` | Seconds between retries |

---

## Test Markers Reference

| Marker | When to use |
|---|---|
| `@pytest.mark.e2e` | Browser UI end-to-end tests |
| `@pytest.mark.accessibility` | WCAG / axe-core tests |
| `@pytest.mark.visual` | Screenshot regression tests |
| `@pytest.mark.api` | HTTP-layer tests (no browser) |
| `@pytest.mark.performance` | Load/timing metric tests |
| `@pytest.mark.smoke` | Fast sanity subset (for PR checks) |
| `@pytest.mark.regression` | Full regression suite |
| `@pytest.mark.regression_write` | Mutating regression tests — auto-skip unless `SANDBOX_ORG_SLUG` is set |
| `@pytest.mark.auth` | Tests that require an authenticated session (`TEST_EMAIL_1` must be set in `.env`) |
| `@pytest.mark.skip_on_ci` | Tests excluded from CI (e.g. locally-dependent flows) |

---

## CI/CD Pipeline

```
Push / PR to main or dev
        │
        ▼
   ┌─────────┐
   │  lint   │  (ruff)
   └────┬────┘
        │
   ┌────┴──────────────────────────────┐
   │         (parallel jobs)           │
   ├──────────┬──────────┬─────────────┤
   │ api-tests│ e2e-tests│  a11y-tests │
   └──────────┴────┬─────┴─────────────┘
                   │   visual-tests
                   │
              ┌────▼────┐
              │ summary │  (GitHub Step Summary)
              └─────────┘

Nightly (02:00 UTC cron):
  → Full suite: e2e + a11y + api + performance + visual
  → Artifacts retained 30 days
  → Slack/email webhook placeholder in scheduled.yml
```

---

## Adding New Tests

1. **Choose the right folder**: `tests/e2e/`, `tests/api/`, etc.
2. **Name the file** `test_<feature>.py`
3. **Add the marker** at the top: `pytestmark = [pytest.mark.e2e]`
4. **Use Page Objects** from `pages/` — create a new one in `pages/` if needed
5. **Run locally** before pushing:
   ```bash
   pytest tests/e2e/test_my_feature.py -v
   ```

### Page Object example
```python
# pages/my_feature_page.py
from pages.base_page import BasePage

class MyFeaturePage(BasePage):
    HEADING = "h1.feature-title"

    def get_title(self) -> str:
        return self.get_text(self.HEADING)
```

### Test example
```python
# tests/e2e/test_my_feature.py
import pytest
from playwright.sync_api import Page
from pages.my_feature_page import MyFeaturePage

pytestmark = [pytest.mark.e2e]

def test_feature_heading(page: Page):
    feature = MyFeaturePage(page)
    feature.navigate_to_path("/my-feature")
    assert "Expected" in feature.get_title()
```

---

## Reports

After each run, reports are written to the `reports/` directory:

| File | Contents |
|---|---|
| `reports/report.html` | Default HTML report (all suites) |
| `reports/e2e_report.html` | E2E-specific HTML report |
| `reports/a11y_report.html` | Accessibility HTML report |
| `reports/accessibility_report.json` | Structured axe violations JSON |
| `reports/performance_metrics.json` | Page timing metrics JSON |
| `screenshots/FAIL_*.png` | Failure screenshots |
| `screenshots/DIFF_*.png` | Visual regression diff images |

---

## Utility Scripts

### `scripts/cleanup_drafts.py` — bulk-cancel DRAFT evaluations

Smoke and regression runs leave `DRAFT` audits behind on the dev backend (one per `New Evaluation` run that didn't reach explicit cleanup). This script cancels them in bulk by calling the same `updateAudit(status: "CANCELLED")` mutation the UI's "Cancel Evaluation" button uses. The ParakhAPI has no `deleteAudit` mutation, so cancellation is the available cleanup path.

```bash
# from the repo root with .venv active
python scripts/cleanup_drafts.py --dry-run                  # preview matches, no writes
python scripts/cleanup_drafts.py                            # cancel all DRAFTs in org 1 (CivicDataLab)
python scripts/cleanup_drafts.py --org-id 5                 # different org
python scripts/cleanup_drafts.py --status DRAFT,CANCELLED   # also re-cancel already-cancelled
python scripts/cleanup_drafts.py --headed                   # show the login browser window
```

How it authenticates: drives a headless Playwright login through Keycloak using `TEST_EMAIL_1` / `TEST_PASSWORD_1` from `.env` (same flow as the `authenticated_page` fixture), reads the access token from `/api/auth/session`, then calls GraphQL directly via `requests`. No extra dependencies beyond what's already in `requirements.txt`.

Defaults assume the dev backend (`https://dev.api.parakh.civicdataspace.in/graphql/`) and frontend (`https://dev.parakh.civicdataspace.in`). Override via `BASE_URL` / `GRAPHQL_URL` env vars when targeting another environment.

---

## Project Structure

```
parakh-test-framework/
├── .github/workflows/
│   ├── ci.yml               # PR + push pipeline
│   └── scheduled.yml        # Nightly regression (02:00 UTC)
├── tests/
│   ├── e2e/                          # Browser UI tests
│   │   ├── test_auth.py
│   │   ├── test_homepage.py
│   │   ├── test_navigation.py
│   │   ├── test_models.py
│   │   ├── test_evaluations.py       # Evaluations list + detail
│   │   ├── test_new_evaluation_smoke.py      # New Evaluation smoke (9 tests)
│   │   └── test_new_evaluation_regression.py # New Evaluation regression (12 tests)
│   ├── accessibility/       # WCAG / axe-core tests
│   ├── visual/              # Screenshot regression
│   ├── api/                 # HTTP-layer tests
│   │   ├── test_graphql.py                  # Anonymous-allowed GraphQL queries
│   │   └── test_graphql_authenticated.py    # Authenticated GraphQL contract tests
│   ├── performance/         # Load & timing tests
│   └── conftest.py          # Shared fixtures (page, authenticated_page, api_client, …)
├── pages/                   # Page Object Models
│   ├── base_page.py             # Base class — all pages inherit from this
│   ├── home_page.py
│   ├── login_page.py
│   ├── dashboard_page.py
│   ├── workspace_page.py        # Role / org selection
│   ├── ai_maker_page.py         # AI Maker dashboard (stats, sidebar)
│   ├── evaluations_page.py      # Evaluations list + detail report
│   ├── new_evaluation_page.py   # New Evaluation wizard — Draft & Auto-Save flow
│   ├── models_page.py           # AI Models list + detail
│   ├── evaluators_page.py       # Evaluators management
│   ├── evaluator_role_page.py   # Evaluator-role specific flows
│   └── prompt_libraries_page.py # Prompt library features
├── utils/
│   ├── config.py            # Environment config
│   ├── helpers.py           # Utility functions
│   ├── reporters.py         # JSON / summary reporting
│   └── test_data_factory.py # Deterministic-prefix factories for write-side tests
├── reports/                 # Generated HTML + JSON reports
├── screenshots/             # Failure + diff screenshots
├── snapshots/               # Visual regression baselines
├── pytest.ini
├── pyproject.toml
├── requirements.txt
├── .env.example
├── CONTRIBUTING.md
├── SECURITY.md
├── LICENSE
└── README.md
```

## Sandbox org for write-side tests

Tests marked `@pytest.mark.regression_write` mutate platform state (creating
evaluations, adding evaluators, etc.) and are **only allowed to run against a
dedicated sandbox organization**. Set `SANDBOX_ORG_SLUG` in `.env` (or as a
GitHub Actions secret) to enable them. When unset, the autouse
`forbid_outside_sandbox` fixture in `tests/conftest.py` skips every
`regression_write` test so production data is never touched accidentally.

---

## License

MIT — see `LICENSE` for details.
