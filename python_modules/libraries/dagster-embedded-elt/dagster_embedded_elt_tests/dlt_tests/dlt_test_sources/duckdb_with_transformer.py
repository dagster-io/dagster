from typing import Optional

import dlt

MOCK_REPOS = [
    {
        "id": 1,
        "name": "example-repo-1",
        "contributors": ["contributor-1", "contributor-2", "contributor-3"],
        "last_modified_dt": "2022-09-08",
    },
    {
        "id": 2,
        "name": "example-repo-2",
        "contributors": ["contributor-1", "contributor-2"],
        "last_modified_dt": "2022-09-11",
    },
    {
        "id": 3,
        "name": "example-repo-3",
        "contributors": ["contributor-1"],
        "last_modified_dt": "2022-09-16",
    },
]

MOCK_ISSUES = {
    1: [
        {"repo_id": 1, "issue_id": 1, "title": "hello-world-1"},
        {"repo_id": 1, "issue_id": 2, "title": "hello-world-2"},
        {"repo_id": 1, "issue_id": 3, "title": "hello-world-3"},
    ],
    2: [
        {"repo_id": 2, "issue_id": 1, "title": "example-1"},
        {"repo_id": 2, "issue_id": 2, "title": "example-2"},
        {"repo_id": 2, "issue_id": 3, "title": "example-3"},
    ],
    3: [
        {"repo_id": 3, "issue_id": 1, "title": "just-one-issue"},
    ],
}


@dlt.source
def pipeline(month: Optional[str] = None):
    @dlt.resource(primary_key="id", write_disposition="merge")
    def repos():
        for d in MOCK_REPOS:
            if d["last_modified_dt"][:-3] == month or not month:
                yield d

    @dlt.transformer(
        primary_key=["repo_id", "issue_id"], write_disposition="merge", data_from=repos
    )
    def repo_issues(repo):
        """Extracted list of issues from repositories."""
        if repo["last_modified_dt"][:-3] == month or not month:
            yield MOCK_ISSUES[repo["id"]]

    return repos, repo_issues
