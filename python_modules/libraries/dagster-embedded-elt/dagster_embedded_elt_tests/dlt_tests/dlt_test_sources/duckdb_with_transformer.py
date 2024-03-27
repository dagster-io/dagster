import dlt

MOCK_REPOS = [
    {"id": 1, "name": "example-repo-1"},
    {"id": 2, "name": "example-repo-2"},
    {"id": 3, "name": "example-repo-3"},
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
def pipeline():
    @dlt.resource(primary_key="id", write_disposition="merge")
    def repos():
        for d in MOCK_REPOS:
            yield d

    @dlt.transformer(
        primary_key=["repo_id", "issue_id"], write_disposition="merge", data_from=repos
    )
    def repo_issues(repo):
        yield MOCK_ISSUES[repo["id"]]

    return repos, repo_issues
