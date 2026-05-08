# Accessibility Findings

axe-core (WCAG 2.1 AA) violations surfaced by `pytest -m accessibility`. Append-only — when a violation is fixed, mark `status: fixed` and the date.

Each row links to the WCAG criterion and the axe rule id (helpful when filing tickets with the frontend team). Real app bugs that block users (not just informational) should also be added to `docs/app_bugs.md`.

| id | rule | wcag | impact | page | element | summary | status | first seen |
|---|---|---|---|---|---|---|---|---|
| a1 | bypass / region | 2.4.1 (A) | serious | `/` (homepage, anonymous) | `<body>` (missing element) | No skip-to-main-content link. Keyboard users cannot bypass nav. Linked to bug #4. | open | 2026-05-08 |
| a2 | color-contrast | 1.4.3 (AA) | serious | Keycloak login (`opub-kc.civicdatalab.in/auth/realms/DataSpace/...`) | form labels / placeholder text | Foreground/background contrast below 4.5:1 for body text. Third-party (Keycloak) — see bug #5. | open (third-party) | 2026-05-08 |
| a3 | link-name | 4.1.2 (A) / 2.4.4 (A) | serious | Keycloak login (footer) | `<a>` containing only `<svg>` (4 social media links) | Icon-only links with no `aria-label` or visible text. Affects GitHub, LinkedIn, Twitter, Facebook links. Third-party — see bug #5. | open (third-party) | 2026-05-08 |

## How to interpret

- **rule** — axe rule id, e.g. `color-contrast`, `aria-required-attr`. Search at https://dequeuniversity.com/rules/axe.
- **wcag** — primary criterion, e.g. `1.4.3` for contrast.
- **impact** — axe's classification: `minor`, `moderate`, `serious`, `critical`. We treat `serious`+`critical` as block-on-merge for new pages, `moderate` as backlog, `minor` as informational.
- **page** — relative URL plus auth state (`/`, `/dashboard/ai-maker/1` (auth), etc.).
- **element** — most specific selector axe could provide; usually a CSS path or aria-label snippet.

## Phase log

- **Phase 2 run 2026-05-08:** 11 a11y tests → 3 fail (1 flake fixed in test code, 2 real bugs filed → bugs #4, #5). 4 pass / 5 skip (env / no-creds) / 2 xfail / 0 fail after fixes.
