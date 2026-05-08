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

(none yet — populated by Phase 4)
