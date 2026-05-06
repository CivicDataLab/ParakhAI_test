# Contributing to the Parakh Test Framework

Thanks for your interest in improving the test suite. This guide covers the
day-to-day workflow: setting up locally, adding a test, and opening a PR.

---

## Local setup

```bash
git clone https://github.com/CivicDataLab/ParakhAI_test.git
cd ParakhAI_test
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install --with-deps chromium
cp .env.example .env       # then fill in TEST_EMAIL_1 / TEST_PASSWORD_1
```

Run the suite locally before opening a PR:

```bash
ruff check .                     # lint must be green
pytest --collect-only            # all tests must collect
pytest -m smoke -v               # fast sanity subset
```

---

## Three-layer architecture

Every change should respect the layering:

| Layer | Allowed | Not allowed |
|---|---|---|
| `tests/` | Assertions, fixture wiring | Raw selectors, page navigation logic |
| `pages/` | Actions, state checks | Assertions, hardcoded URLs |
| `locators/` | CSS / text selectors | Any logic |

If a test references a raw selector, the fix is to add it to `locators/`
and route through the page object — not to inline it.

---

## Adding a test

1. Place the file in `tests/<suite>/` named `test_<feature>.py`.
2. Set the marker at module level: `pytestmark = [pytest.mark.<marker>]`.
3. If the feature has a new page, add a `pages/<feature>_page.py` extending
   `BasePage` and a matching `locators/<feature>_locators.py`.
4. For login-required tests, use the `authenticated_page` fixture and add
   `@pytest.mark.auth`.
5. For tests that mutate platform state, use the `regression_write` marker —
   they auto-skip unless `SANDBOX_ORG_SLUG` is set.

### Selector conventions

Use comma-separated CSS fallback strings with `aria-*` attributes preferred
over class names. Example:

```python
SUBMIT_BUTTON = (
    'button[aria-label="Submit"], '
    'button:has-text("Submit"), '
    '[data-testid="submit-button"]'
)
```

This tolerates minor UI changes without churning the test suite.

---

## Markers reference

| Marker | When to use |
|---|---|
| `e2e` | Browser UI end-to-end tests |
| `accessibility` | WCAG / axe-core tests |
| `visual` | Screenshot regression tests |
| `api` | HTTP-layer tests (no browser) |
| `performance` | Load/timing metric tests |
| `smoke` | Fast sanity subset (PR checks) |
| `regression` | Full regression suite |
| `regression_write` | Tests that mutate platform state — sandbox org only |
| `auth` | Tests that require an authenticated session |

---

## Pull requests

- Keep PRs small and focused.
- Include the `pytest -v` output for the tests you added or changed.
- Lint must be green (`ruff check .`).
- If you change a page object, update its locator file and any dependent tests
  in the same PR.
- Visual regression baselines go in `snapshots/` — update them by deleting
  the stale PNG and re-running the specific test.

---

## Reporting bugs

Open an issue with:

- Steps to reproduce
- Expected vs actual behavior
- Test runner output (or screenshot from `screenshots/FAIL_*.png` if relevant)
- Environment (`pytest --version`, `playwright --version`, OS)

For security issues, see [SECURITY.md](SECURITY.md) — please do not open a
public issue.
