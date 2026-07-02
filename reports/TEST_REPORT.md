# Parakh Test Framework — Test Report

**Generated:** 2026-07-01 19:32 UTC  
**Environment:** `staging` — https://dev.parakh.civicdataspace.in  
**Browser:** `chromium`  
**Overall result:** ❌ FAILED

## Summary

| Metric | Value |
| ------ | ----- |
| Total tests | 48 |
| Passed | 12 ✅ |
| Failed | 9 ❌ |
| Skipped | 25 ⏭️ |
| Errors | 2 💥 |
| Pass rate | 25.0% |
| Duration | 0.00s |

## Results by Suite

### E2E (48 tests — ✅ 12 / ❌ 9 / ⏭️ 25)

| Test | Result | Duration |
| ---- | ------ | -------- |
| `test_create_bulk_audit_returns_draft` | ⏭️ skipped | 0.00s |
| `test_run_bulk_audit_transitions_status` | ⏭️ skipped | 0.00s |
| `test_bulk_audit_reaches_queued_or_in_progress` | ⏭️ skipped | 0.00s |
| `test_evaluation_detail_page_loads_for_pending_review[chromium]` | ✅ passed | 0.00s |
| `test_evaluator_review_section_is_visible_on_pending_review[chromium]` | ✅ passed | 0.00s |
| `test_submit_review_button_visible_on_pending_review[chromium]` | ✅ passed | 0.00s |
| `test_completed_eval_detail_shows_status_badge[chromium]` | 💥 error | 0.00s |
| `test_completed_eval_detail_overview_renders[chromium]` | 💥 error | 0.00s |
| `test_completed_eval_shows_generate_or_download_report[chromium]` | ❌ failed | 0.00s |
| `test_playground_workspace_loads_for_in_progress_audit[chromium]` | ⏭️ skipped | 0.00s |
| `test_playground_prompt_input_accepts_text[chromium]` | ⏭️ skipped | 0.00s |
| `test_call_model_button_is_visible_when_prompt_entered[chromium]` | ⏭️ skipped | 0.00s |
| `test_call_model_produces_output_panel[chromium]` | ⏭️ skipped | 0.00s |
| `test_call_model_increments_test_case_counter[chromium]` | ⏭️ skipped | 0.00s |
| `test_add_issue_button_appears_after_model_call[chromium]` | ⏭️ skipped | 0.00s |
| `test_generate_reason_button_visible_in_issue_form[chromium]` | ⏭️ skipped | 0.00s |
| `test_finish_button_present_after_test_case_submitted[chromium]` | ⏭️ skipped | 0.00s |
| `test_page_loads_at_correct_url[chromium]` | ✅ passed | 0.00s |
| `test_page_heading_visible[chromium]` | ✅ passed | 0.00s |
| `test_page_title_is_set[chromium]` | ✅ passed | 0.00s |
| `test_page_subheading_visible[chromium]` | ✅ passed | 0.00s |
| `test_add_evaluator_button_visible[chromium]` | ✅ passed | 0.00s |
| `test_evaluator_cards_or_empty_state[chromium]` | ✅ passed | 0.00s |
| `test_evaluator_card_count_is_non_negative[chromium]` | ✅ passed | 0.00s |
| `test_at_least_one_evaluator_card_present[chromium]` | ⏭️ skipped | 0.00s |
| `test_remove_button_present_on_each_card[chromium]` | ⏭️ skipped | 0.00s |
| `test_add_button_opens_dialog[chromium]` | ⏭️ skipped | 0.00s |
| `test_dialog_email_input_is_present[chromium]` | ⏭️ skipped | 0.00s |
| `test_dialog_cancel_closes_dialog[chromium]` | ⏭️ skipped | 0.00s |
| `test_add_button_opens_dialog[chromium]` | ⏭️ skipped | 0.00s |
| `test_dialog_cancel_dismisses[chromium]` | ⏭️ skipped | 0.00s |
| `test_remove_button_visible_on_existing_row[chromium]` | ⏭️ skipped | 0.00s |
| `test_user2_sees_pending_invitation_after_assignment[chromium]` | ⏭️ skipped | 0.00s |
| `test_two_sessions_do_not_interfere[chromium]` | ⏭️ skipped | 0.00s |
| `test_wizard_opens_and_renders_configuration_tab[chromium]` | ❌ failed | 0.00s |
| `test_evaluation_name_is_editable[chromium]` | ❌ failed | 0.00s |
| `test_audit_type_domain_forces_manual_mode[chromium]` | ❌ failed | 0.00s |
| `test_advance_to_test_cases_tab_creates_draft[chromium]` | ❌ failed | 0.00s |
| `test_dataset_table_visible_in_automated_mode[chromium]` | ❌ failed | 0.00s |
| `test_run_evaluation_button_disabled_with_no_selection[chromium]` | ❌ failed | 0.00s |
| `test_pending_audit_visible_in_evaluations_list[chromium]` | ⏭️ skipped | 0.00s |
| `test_generate_report_button_is_visible[chromium]` | ❌ failed | 0.00s |
| `test_generate_report_button_click_shows_download[chromium]` | ⏭️ skipped | 0.00s |
| `test_download_report_button_is_visible_after_generation[chromium]` | ❌ failed | 0.00s |
| `test_download_report_button_triggers_download_or_navigation[chromium]` | ⏭️ skipped | 0.00s |
| `test_download_report_no_console_errors[chromium]` | ✅ passed | 0.00s |
| `test_add_auditor_to_organization` | ✅ passed | 0.00s |
| `test_run_evaluation_creates_pending_audit_via_api` | ⏭️ skipped | 0.00s |

## Failure Details

### 💥 `tests/e2e/test_bulk_evaluation_flow.py::TestBulkEvaluationStatusUI::test_completed_eval_detail_shows_status_badge[chromium]`

### 💥 `tests/e2e/test_bulk_evaluation_flow.py::TestBulkEvaluationStatusUI::test_completed_eval_detail_overview_renders[chromium]`

### ❌ `tests/e2e/test_bulk_evaluation_flow.py::TestBulkEvaluationStatusUI::test_completed_eval_shows_generate_or_download_report[chromium]`

```
[gw0] darwin -- Python 3.11.15 /Users/home/CivicDataSpace/ParakhAI_test/.venv/bin/python3.11
E   AssertionError: A COMPLETED evaluation must show either 'Generate Report' or 'Download Report' button
    assert (False or False)
```

**Screenshot:** `/Users/home/CivicDataSpace/ParakhAI_test/screenshots/20260702_004351_FAIL_FAST_test_completed_eval_shows_generate_or_download_report[chromium].png`

### ❌ `tests/e2e/test_new_evaluation_full_flow.py::TestNewEvaluationConfigurationTab::test_wizard_opens_and_renders_configuration_tab[chromium]`

```
[gw0] darwin -- Python 3.11.15 /Users/home/CivicDataSpace/ParakhAI_test/.venv/bin/python3.11
E   playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 30000ms exceeded.
    Call log:
      - waiting for locator("button:has-text('New Evaluation'), a:has-text('New Evaluation')").first to be visible
```

**Screenshot:** `/Users/home/CivicDataSpace/ParakhAI_test/screenshots/20260702_004949_FAIL_FAST_test_wizard_opens_and_renders_configuration_tab[chromium].png`

**Screenshot:** `/Users/home/CivicDataSpace/ParakhAI_test/screenshots/20260702_005025_FAIL_FAST_test_wizard_opens_and_renders_configuration_tab[chromium].png`

**Screenshot:** `/Users/home/CivicDataSpace/ParakhAI_test/screenshots/20260702_005100_FAIL_FAST_test_wizard_opens_and_renders_configuration_tab[chromium].png`

### ❌ `tests/e2e/test_new_evaluation_full_flow.py::TestNewEvaluationConfigurationTab::test_evaluation_name_is_editable[chromium]`

```
[gw0] darwin -- Python 3.11.15 /Users/home/CivicDataSpace/ParakhAI_test/.venv/bin/python3.11
E   playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 30000ms exceeded.
    Call log:
      - waiting for locator("button:has-text('New Evaluation'), a:has-text('New Evaluation')").first to be visible
```

**Screenshot:** `/Users/home/CivicDataSpace/ParakhAI_test/screenshots/20260702_005134_FAIL_FAST_test_evaluation_name_is_editable[chromium].png`

**Screenshot:** `/Users/home/CivicDataSpace/ParakhAI_test/screenshots/20260702_005211_FAIL_FAST_test_evaluation_name_is_editable[chromium].png`

**Screenshot:** `/Users/home/CivicDataSpace/ParakhAI_test/screenshots/20260702_005247_FAIL_FAST_test_evaluation_name_is_editable[chromium].png`

### ❌ `tests/e2e/test_new_evaluation_full_flow.py::TestNewEvaluationConfigurationTab::test_audit_type_domain_forces_manual_mode[chromium]`

```
[gw0] darwin -- Python 3.11.15 /Users/home/CivicDataSpace/ParakhAI_test/.venv/bin/python3.11
E   playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 30000ms exceeded.
    Call log:
      - waiting for locator("button:has-text('New Evaluation'), a:has-text('New Evaluation')").first to be visible
```

**Screenshot:** `/Users/home/CivicDataSpace/ParakhAI_test/screenshots/20260702_005325_FAIL_FAST_test_audit_type_domain_forces_manual_mode[chromium].png`

**Screenshot:** `/Users/home/CivicDataSpace/ParakhAI_test/screenshots/20260702_005408_FAIL_FAST_test_audit_type_domain_forces_manual_mode[chromium].png`

**Screenshot:** `/Users/home/CivicDataSpace/ParakhAI_test/screenshots/20260702_005444_FAIL_FAST_test_audit_type_domain_forces_manual_mode[chromium].png`

### ❌ `tests/e2e/test_new_evaluation_full_flow.py::TestNewEvaluationTestCasesTab::test_advance_to_test_cases_tab_creates_draft[chromium]`

```
[gw0] darwin -- Python 3.11.15 /Users/home/CivicDataSpace/ParakhAI_test/.venv/bin/python3.11
E   playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 30000ms exceeded.
    Call log:
      - waiting for locator("button:has-text('New Evaluation'), a:has-text('New Evaluation')").first to be visible
```

**Screenshot:** `/Users/home/CivicDataSpace/ParakhAI_test/screenshots/20260702_005520_FAIL_FAST_test_advance_to_test_cases_tab_creates_draft[chromium].png`

**Screenshot:** `/Users/home/CivicDataSpace/ParakhAI_test/screenshots/20260702_005555_FAIL_FAST_test_advance_to_test_cases_tab_creates_draft[chromium].png`

**Screenshot:** `/Users/home/CivicDataSpace/ParakhAI_test/screenshots/20260702_005632_FAIL_FAST_test_advance_to_test_cases_tab_creates_draft[chromium].png`

### ❌ `tests/e2e/test_new_evaluation_full_flow.py::TestNewEvaluationTestCasesTab::test_dataset_table_visible_in_automated_mode[chromium]`

```
[gw0] darwin -- Python 3.11.15 /Users/home/CivicDataSpace/ParakhAI_test/.venv/bin/python3.11
E   playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 30000ms exceeded.
    Call log:
      - waiting for locator("button:has-text('New Evaluation'), a:has-text('New Evaluation')").first to be visible
```

**Screenshot:** `/Users/home/CivicDataSpace/ParakhAI_test/screenshots/20260702_005705_FAIL_FAST_test_dataset_table_visible_in_automated_mode[chromium].png`

**Screenshot:** `/Users/home/CivicDataSpace/ParakhAI_test/screenshots/20260702_005740_FAIL_FAST_test_dataset_table_visible_in_automated_mode[chromium].png`

**Screenshot:** `/Users/home/CivicDataSpace/ParakhAI_test/screenshots/20260702_005815_FAIL_FAST_test_dataset_table_visible_in_automated_mode[chromium].png`

### ❌ `tests/e2e/test_new_evaluation_full_flow.py::TestNewEvaluationRunEvaluation::test_run_evaluation_button_disabled_with_no_selection[chromium]`

```
[gw0] darwin -- Python 3.11.15 /Users/home/CivicDataSpace/ParakhAI_test/.venv/bin/python3.11
E   playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 30000ms exceeded.
    Call log:
      - waiting for locator("button:has-text('New Evaluation'), a:has-text('New Evaluation')").first to be visible
```

**Screenshot:** `/Users/home/CivicDataSpace/ParakhAI_test/screenshots/20260702_005848_FAIL_FAST_test_run_evaluation_button_disabled_with_no_selection[chromium].png`

**Screenshot:** `/Users/home/CivicDataSpace/ParakhAI_test/screenshots/20260702_005923_FAIL_FAST_test_run_evaluation_button_disabled_with_no_selection[chromium].png`

**Screenshot:** `/Users/home/CivicDataSpace/ParakhAI_test/screenshots/20260702_010000_FAIL_FAST_test_run_evaluation_button_disabled_with_no_selection[chromium].png`

### ❌ `tests/e2e/test_report_download.py::TestGenerateReportButton::test_generate_report_button_is_visible[chromium]`

```
[gw0] darwin -- Python 3.11.15 /Users/home/CivicDataSpace/ParakhAI_test/.venv/bin/python3.11
E   AssertionError: Either 'Generate Report' or 'Download Report' must be visible on a COMPLETED evaluation detail page
    assert (False or False)
```

**Screenshot:** `/Users/home/CivicDataSpace/ParakhAI_test/screenshots/20260702_010014_FAIL_FAST_test_generate_report_button_is_visible[chromium].png`

**Screenshot:** `/Users/home/CivicDataSpace/ParakhAI_test/screenshots/20260702_010031_FAIL_FAST_test_generate_report_button_is_visible[chromium].png`

**Screenshot:** `/Users/home/CivicDataSpace/ParakhAI_test/screenshots/20260702_010046_FAIL_FAST_test_generate_report_button_is_visible[chromium].png`

### ❌ `tests/e2e/test_report_download.py::TestDownloadReportButton::test_download_report_button_is_visible_after_generation[chromium]`

```
[gw0] darwin -- Python 3.11.15 /Users/home/CivicDataSpace/ParakhAI_test/.venv/bin/python3.11
E   AssertionError: Download Report button must appear on a COMPLETED evaluation (possibly after Generate)
    assert (False or False)
     +  where False = is_download_button_visible()
     +    where is_download_button_visible = <pages.evaluation_detail_page.EvaluationDetailPage object at 0x108011bd0>.is_download_button_visible
     +  and   False = is_generate_report_button_visible()
     +    where is_generate_report_button_visible = <pages.evaluation_detail_page.EvaluationDetailPage object at 0x108011bd0>.is_generate_report_button_visible
```

**Screenshot:** `/Users/home/CivicDataSpace/ParakhAI_test/screenshots/20260702_010122_FAIL_FAST_test_download_report_button_is_visible_after_generation[chromium].png`

**Screenshot:** `/Users/home/CivicDataSpace/ParakhAI_test/screenshots/20260702_010149_FAIL_FAST_test_download_report_button_is_visible_after_generation[chromium].png`

**Screenshot:** `/Users/home/CivicDataSpace/ParakhAI_test/screenshots/20260702_010216_FAIL_FAST_test_download_report_button_is_visible_after_generation[chromium].png`

---

_Generated by the Parakh Test Framework report generator._