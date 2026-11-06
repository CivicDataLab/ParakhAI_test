"""Unauthenticated POST must not run audit-lifecycle mutations.

The older GET-based check in test_security.py is vacuous (GET never runs a
mutation); this posts for real. Inputs use nonexistent ids so a missing auth
check cannot create or change production data.
"""

import pytest
import requests

from utils.config import Config

pytestmark = [pytest.mark.api, pytest.mark.security]

GRAPHQL = Config.graphql_endpoint()
_BOGUS = "999999999"

_CASES = {
    "createBlankAudit": (
        "mutation($i: CreateBlankAuditInput!){ createBlankAudit(input:$i){ success audit{ id } } }",
        {"modelId": _BOGUS},
    ),
    "updateAudit": (
        "mutation($i: UpdateAuditInput!){ updateAudit(input:$i){ success audit{ id } } }",
        {"auditId": _BOGUS, "status": "CANCELLED"},
    ),
    "runAudit": (
        "mutation($i: RunAuditInput!){ runAudit(input:$i){ success audit{ id } } }",
        {"auditId": _BOGUS},
    ),
}


@pytest.mark.parametrize("field", list(_CASES), ids=list(_CASES))
def test_unauthenticated_post_mutation_is_rejected(api_client: requests.Session, field):
    query, variables = _CASES[field]
    try:
        resp = api_client.post(
            GRAPHQL, json={"query": query, "variables": {"i": variables}}, timeout=20
        )
    except requests.exceptions.ConnectionError:
        pytest.skip("GraphQL endpoint unreachable")
    assert resp.status_code != 500, f"{field} unauthenticated returned 500"
    if resp.status_code != 200:
        return
    body = resp.json()
    result = (body.get("data") or {}).get(field)
    assert body.get("errors") or not (isinstance(result, dict) and result.get("success")), (
        f"{field} succeeded without authentication: {body}"
    )
