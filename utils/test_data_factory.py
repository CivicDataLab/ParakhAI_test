"""
Deterministic-prefix factories for write-side regression tests.

Every entity created by a regression_write test should be named via these
helpers so leaks are greppable: `git grep "reg-eval-"` against logs/sandbox
quickly reveals what didn't get cleaned up.
"""

import os
import secrets


def _run_id() -> str:
    """GitHub Actions run id when in CI, else 'local'."""
    return os.getenv("GITHUB_RUN_ID", "local")


def unique_evaluation_name() -> str:
    """Return a deterministic-prefix evaluation name."""
    return f"reg-eval-{_run_id()}-{secrets.token_hex(3)}"


def unique_evaluator_email() -> str:
    """Return a deterministic-prefix evaluator email."""
    return f"reg+{secrets.token_hex(4)}@sandbox.parakh.test"


def unique_audit_input(model_id: str, model_version_id: str | None = None) -> dict:
    """Return a valid RequestAuditInput-shaped dict for mutation tests."""
    return {
        "modelId": model_id,
        "name": unique_evaluation_name(),
        "modelVersionId": model_version_id,
    }
