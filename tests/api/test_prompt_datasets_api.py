"""
Prompt dataset listing (ParakhAI-Backend#145).

#145 sends the request's `organization` header to DataSpace (the org's own
datasets plus public datasets of other orgs), lists PUBLISHED datasets only,
and adds `promptDatasetsPage(search, limit, offset, ...) { totalCount items }`
for server-side paging. The `promptDatasets` contract is unchanged.

Gated on the schema, not on the PR's merge state: #145 merges to main (prod)
while dev runs behind main, so "merged" doesn't mean the API under test has it.
"""

import pytest

pytestmark = [pytest.mark.api, pytest.mark.regression, pytest.mark.auth]

PAGE = """
query ($search: String, $limit: Int!, $offset: Int!) {
  promptDatasetsPage(search: $search, limit: $limit, offset: $offset) {
    totalCount items { id title status }
  }
}
"""
LIST = "{ promptDatasets(limit: 200) { id status organization } }"


@pytest.fixture(autouse=True, scope="module")
def _requires_pr145(authenticated_graphql_client):
    r = authenticated_graphql_client('{ __type(name: "Query") { fields { name } } }')
    if "promptDatasetsPage" not in {f["name"] for f in r["data"]["__type"]["fields"]}:
        pytest.skip("ParakhAI-Backend#145 not deployed here (no promptDatasetsPage)")


def _gql(client, query, **variables):
    result = client(query, variables=variables or None, method="POST")
    assert not result.get("errors"), f"GraphQL errors: {result.get('errors')}"
    return result["data"]


def _page(client, limit=10, offset=0, search=None):
    return _gql(client, PAGE, limit=limit, offset=offset, search=search)["promptDatasetsPage"]


def test_page_returns_published_items_with_total(authenticated_graphql_client):
    page = _page(authenticated_graphql_client, limit=5)
    assert page["totalCount"] >= len(page["items"]) > 0, page
    assert len(page["items"]) <= 5
    assert {d["status"] for d in page["items"]} == {"PUBLISHED"}


def test_pages_do_not_overlap(authenticated_graphql_client):
    first = _page(authenticated_graphql_client, limit=5)
    if first["totalCount"] <= 5:
        pytest.skip(f"Only {first['totalCount']} datasets, no second page")
    second = _page(authenticated_graphql_client, limit=5, offset=5)
    assert second["totalCount"] == first["totalCount"]
    overlap = {d["id"] for d in first["items"]} & {d["id"] for d in second["items"]}
    assert second["items"] and not overlap, f"offset=5 repeated {overlap}"


def test_search_narrows_by_title(authenticated_graphql_client):
    total = _page(authenticated_graphql_client)["totalCount"]
    hits = _page(authenticated_graphql_client, limit=100, search="kcc")
    assert 0 < hits["totalCount"] < total, f"search 'kcc': {hits['totalCount']} of {total}"
    wrong = [d["title"] for d in hits["items"] if "kcc" not in d["title"].lower()]
    assert not wrong, f"Titles not matching 'kcc': {wrong}"


@pytest.mark.security
def test_list_never_returns_unpublished_datasets(authenticated_graphql_client):
    """Drafts must not be listed. Before #145, org-less drafts reached every org."""
    rows = _gql(authenticated_graphql_client, LIST)["promptDatasets"]
    leaked = [(d["id"], (d["organization"] or {}).get("id"), d["status"]) for d in rows if d["status"] != "PUBLISHED"]
    assert not leaked, f"Unpublished datasets listed: {leaked}"
