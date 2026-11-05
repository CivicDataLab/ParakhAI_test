"""Evaluation option matrix at the API layer + matrix definition self-check.

- TestMatrixDefinition: pure data checks on tests/data/evaluation_matrix.py (no network).
- TestEvaluationOptionRoundTrip: every evaluator x domain pair (9) is accepted by
  updateAudit and read back unchanged (write; sandbox-gated; drafts are cancelled).
"""

from itertools import product

import pytest

from tests.data.evaluation_matrix import DOMAINS, EVALUATORS, _selfcheck, all_combos, combos_for
from tests.data.test_data import TestGraphQL, first_org_model_id

_AUDIT_Q = "query($id: ID!){ audit(auditId:$id){ id status auditType auditScope evaluationMode } }"


@pytest.mark.smoke
@pytest.mark.regression
class TestMatrixDefinition:
    def test_selfcheck_passes(self):
        _selfcheck()

    def test_full_space_is_135_unique_cases(self):
        ids = [c.id for c in all_combos()]
        assert len(ids) == len(set(ids)) == 135

    def test_selection_is_opt_in(self):
        assert combos_for("") == [] and len(combos_for("pairwise")) == 14


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.regression_write
@pytest.mark.auth
class TestEvaluationOptionRoundTrip:
    @pytest.mark.parametrize("evaluator,domain", list(product(EVALUATORS, DOMAINS)))
    def test_evaluator_and_scope_round_trip(
        self, authenticated_graphql_client, sandbox_org, cleanup_evaluation, evaluator, domain
    ):
        client = authenticated_graphql_client
        model_id = first_org_model_id(client)
        if not model_id:
            pytest.skip("No non-Opus org model available")
        created = client(
            TestGraphQL.MUTATION_CREATE_BLANK_AUDIT,
            variables={"input": {"modelId": model_id}},
            method="POST",
        )
        audit_id = str((((created.get("data") or {}).get("createBlankAudit") or {}).get("audit") or {}).get("id") or "")
        assert audit_id, created
        cleanup_evaluation.append(audit_id)

        upd = client(
            TestGraphQL.MUTATION_UPDATE_AUDIT,
            variables={"input": {"auditId": audit_id, "auditType": evaluator, "auditScope": domain,
                                 "evaluationMode": "bulk", "name": f"API matrix {evaluator}/{domain}"}},
            method="POST",
        )
        assert ((upd.get("data") or {}).get("updateAudit") or {}).get("success"), upd

        got = ((client(_AUDIT_Q, variables={"id": audit_id}).get("data") or {}).get("audit")) or {}
        assert (got.get("auditType") or "").lower() == evaluator, got
        assert (got.get("auditScope") or "").lower() == domain, got
