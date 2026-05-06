# Security Policy

## Reporting a vulnerability

If you discover a security issue in this test framework or in the Parakh
platform it tests, please **do not open a public GitHub issue**. Instead,
report it privately so we can address it before any details become public.

**Email:** security@civicdatalab.in

Please include:

- A description of the issue and its potential impact
- Steps to reproduce (proof-of-concept code, screenshots, or logs)
- The affected component (this repo, ParakhAPI, ParakhAI frontend, etc.)
- Your name / handle for credit (optional)

We aim to acknowledge reports within **3 business days** and provide a
remediation timeline within **10 business days**.

---

## Scope

This repository is a Playwright test suite. It does **not** ship runtime code
for end users. Vulnerabilities most relevant to this repo include:

- Credentials accidentally committed to git history
- Test fixtures that leak production data
- Dependencies (in `requirements.txt`) with known CVEs
- CI workflows that expose secrets in logs or artifacts

Vulnerabilities in the Parakh platform itself (the system under test) should
be reported through the same channel — we triage and forward to the platform
team.

---

## Out of scope

- Test failures that reveal platform bugs — open a normal issue
- Flaky tests
- Visual regression diffs from intentional UI changes
- Accessibility findings (open a normal issue or PR)

---

## Hall of fame

We credit responsible disclosures here. Reach out at security@civicdatalab.in.
