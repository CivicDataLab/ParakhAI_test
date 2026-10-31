# Accessibility Findings

axe-core (WCAG 2.1 AA) violations surfaced by `pytest -m accessibility`. Append-only — when a violation is fixed, mark `status: fixed` and the date.

Each row links to the WCAG criterion and the axe rule id (helpful when filing tickets with the frontend team). Real app bugs that block users (not just informational) should also be added to `docs/app_bugs.md`.

| id | rule | wcag | impact | page | element | summary | status | first seen |
|---|---|---|---|---|---|---|---|---|
| a1 | bypass / region | 2.4.1 (A) | serious | `/` (homepage, anonymous) | `<body>` (missing element) | No skip-to-main-content link. Keyboard users cannot bypass nav. Linked to bug #4. | open | 2026-05-08 |
| a2 | color-contrast | 1.4.3 (AA) | serious | Keycloak login (`opub-kc.civicdatalab.in/auth/realms/DataSpace/...`) | form labels / placeholder text | Foreground/background contrast below 4.5:1 for body text. Third-party (Keycloak) — see bug #5. | open (third-party) | 2026-05-08 |
| a3 | link-name | 4.1.2 (A) / 2.4.4 (A) | serious | Keycloak login (footer) | `<a>` containing only `<svg>` (4 social media links) | Icon-only links with no `aria-label` or visible text. Affects GitHub, LinkedIn, Twitter, Facebook links. Third-party — see bug #5. | open (third-party) | 2026-05-08 |
| a4 | heading-order / page-has-heading-one | 1.3.1 (A) | serious | `/dashboard/ai-maker/1` (auth) | `<main>` (no h1/h2/h3 anywhere) | No heading elements at all — the Overview widget that would host the page heading never mounts because its data fetch hangs indefinitely. Linked to bug #14 (and bug #13's backend root cause). | open | 2026-07-10 |
| a5 | color-contrast | 1.4.3 (AA) | serious | `/` (anonymous, hydrated) | `button.bg-[#E8E4FF]` | Active feature tab text #6849EE on #E8E4FF = 4.49:1. Linked to bug #31. | open | 2026-10-31 |
| a6 | link-name | 4.1.2 (A) / 2.4.4 (A) | serious | `/` (anonymous, hydrated) | `footer a.w-10.h-10` x4 | Footer social icons unnamed; only visible after hydration. Same as bug #9. | open | 2026-10-31 |
| a7 | (manual) name-role-value | 4.1.2 (A) / 1.4.1 (A) | serious | `/` | feature tab `<button>`s | Selected tab not exposed via aria-pressed/selected/current. Bug #32. | open | 2026-10-31 |
| a8 | (manual) language of parts | 3.1.2 (AA) | moderate | `/` | hero `h2 span.block` | Hindi/Odia/Assamese words with no `lang`. Bug #33. | open | 2026-10-31 |
| a9 | image-alt | 1.1.1 (A) | critical | `/api/auth/signin` | `img#provider-logo` | NextAuth provider logo has no alt. Bug #34. | open | 2026-10-31 |
| a10 | aria-dialog-name | 4.1.2 (A) | serious | `/` at 390px, menu open | `[role=dialog]` | Mobile menu sheet unnamed. Bug #38. | open | 2026-10-31 |
| a11 | button-name | 4.1.2 (A) | critical | `/` at 390px, menu open | `.Button-module_kindTertiary__p3qgr` | Close (X) button unnamed. Bug #39. | open | 2026-10-31 |
| a12 | (manual) focus order | 2.4.3 (A) | moderate | `/` at 390px | hamburger button | Focus drops to `<body>` after the menu closes. Bug #40. | open | 2026-10-31 |

## How to interpret

- **rule** — axe rule id, e.g. `color-contrast`, `aria-required-attr`. Search at https://dequeuniversity.com/rules/axe.
- **wcag** — primary criterion, e.g. `1.4.3` for contrast.
- **impact** — axe's classification: `minor`, `moderate`, `serious`, `critical`. We treat `serious`+`critical` as block-on-merge for new pages, `moderate` as backlog, `minor` as informational.
- **page** — relative URL plus auth state (`/`, `/dashboard/ai-maker/1` (auth), etc.).
- **element** — most specific selector axe could provide; usually a CSS path or aria-label snippet.

## Phase log

- **Phase 2 run 2026-05-08:** 11 a11y tests → 3 fail (1 flake fixed in test code, 2 real bugs filed → bugs #4, #5). 4 pass / 5 skip (env / no-creds) / 2 xfail / 0 fail after fixes.
- **Phase 7 run 2026-07-10:** 34 a11y tests (public + authenticated) → 1 fail, reproduced consistently (not flaky). Root-caused to dashboard overview widget hang; filed bug #14 / finding a4 and xfailed. 14 pass / 9 skip / 10 xfail / 0 fail after triage.
- **Phase 14 run 2026-10-31:** anonymous review of the hydrated homepage, sign-in page and mobile menu. a5-a12 added (bugs #31-#34, #38-#40). The pre-existing homepage axe test scans the pre-hydration skeleton, so a5/a6 were invisible to it.
