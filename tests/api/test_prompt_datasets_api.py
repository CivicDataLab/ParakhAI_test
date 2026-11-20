"""
promptDatasets org scoping + SDK filters (ParakhAI-Backend#145).

#145 sends the request's `organization` header to DataSpace, which returns the
org's own datasets (drafts included) plus, with includePublic, every PUBLISHED
prompt dataset of other orgs. Filters: status (PromptDatasetStatus enum),
includePublic, limit, offset. resources.schema is a JSON leaf.

Gated on the schema, not on the PR's merge state: #145 merges to main (prod)
while dev runs behind main, so "merged" doesn't mean the API under test has it.
"""

import pytest

from utils.config import Config

pytestmark = [pytest.mark.api, pytest.mark.regression, pytest.mark.auth]

QUERY = """
query ($status: PromptDatasetStatus, $includePublic: Boolean!, $limit: Int!, $offset: Int!) {
  promptDatasets(status: $status, includePublic: $includePublic, limit: $limit, offset: $offset) {
    id status isPublic organization resources { schema }
  }
}
"""

ORG_ID = str(getattr(Config, "CIVICDATALAB_ORG_ID", 1))


@pytest.fixture(autouse=True, scope="module")
def _requires_pr145(authenticated_graphql_client):
    r = authenticated_graphql_client('{ __type(name: "Query") { fields { name args { name } } } }')
    args = {a["name"] for f in r["data"]["__type"]["fields"] if f["name"] == "promptDatasets" for a in f["args"]}
    if "includePublic" not in args:
        pytest.skip(f"ParakhAI-Backend#145 not deployed at {Config.graphql_endpoint()} (promptDatasets args: {sorted(args)})")


def _list(client, **variables):
    variables = {"includePublic": True, "limit": 200, "offset": 0, **variables}
    result = client(QUERY, variables=variables, method="POST")
    assert not result.get("errors"), f"promptDatasets errored: {result.get('errors')}"
    return result["data"]["promptDatasets"]


def _org_id(ds):
    return str((ds.get("organization") or {}).get("id"))


def test_new_filters_and_json_schema_are_accepted(authenticated_graphql_client):
    datasets = _list(authenticated_graphql_client, status="PUBLISHED", limit=5)
    assert datasets, "Expected at least one PUBLISHED prompt dataset"
    assert len(datasets) <= 5, f"limit=5 returned {len(datasets)}"
    assert {d["status"] for d in datasets} == {"PUBLISHED"}, [d["status"] for d in datasets]
    for d in datasets:
        for r in d["resources"]:
            assert isinstance(r["schema"], list), f"schema must be a JSON list, got {r['schema']!r}"


@pytest.mark.security
def test_other_orgs_contribute_only_published_datasets(authenticated_graphql_client):
    """Drafts and archived datasets of other orgs must never reach this org."""
    foreign = [d for d in _list(authenticated_graphql_client) if _org_id(d) != ORG_ID]
    if not foreign:
        pytest.skip("No other org has a published prompt dataset on this environment")
    leaked = [(d["id"], _org_id(d), d["status"]) for d in foreign if d["status"] != "PUBLISHED"]
    assert not leaked, f"Unpublished datasets of other orgs returned: {leaked}"


@pytest.mark.security
def test_include_public_false_returns_only_own_org(authenticated_graphql_client):
    with_public = _list(authenticated_graphql_client)
    own_only = _list(authenticated_graphql_client, includePublic=False)
    others = sorted({_org_id(d) for d in own_only} - {ORG_ID})
    assert not others, f"includePublic=false returned datasets of orgs {others}"
    if not any(_org_id(d) != ORG_ID for d in with_public):
        pytest.skip("No foreign published datasets, so includePublic cannot narrow the list")
    assert len(own_only) < len(with_public)
