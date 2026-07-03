"""
Deterministic-prefix factories for write-side regression tests.

Every entity created by a regression_write test should be named via these
helpers so leaks are greppable: `git grep "reg-eval-"` against logs/sandbox
quickly reveals what didn't get cleaned up.
"""

import os
import secrets

# Excluded from random model selection: 'New AI Model' is the ghost placeholder
# created by the CDS-002 "Add New AI Model" bug (empty metadata, no working
# access method); 'xAI: Grok 4.1 Fast' is deprecated on the platform.
EXCLUDED_MODEL_NAMES = {"New AI Model", "xAI: Grok 4.1 Fast"}


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


def pick_random_valid_model(models: list[dict]) -> dict | None:
    """Pick a random model from a GraphQL `aiModels`/`myModels` result list,
    excluding EXCLUDED_MODEL_NAMES (placeholder + deprecated models).

    `models` items must have a "name" key. Falls back to the first model if
    every entry is excluded; returns None for an empty list.
    """
    import random

    if not models:
        return None
    valid = [m for m in models if m.get("name") not in EXCLUDED_MODEL_NAMES]
    return random.choice(valid) if valid else models[0]
