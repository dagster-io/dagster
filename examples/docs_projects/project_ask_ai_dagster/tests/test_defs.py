from unittest.mock import MagicMock

import dagster as dg
from langchain_core.documents import Document
from project_ask_ai_dagster.definitions import defs as _raw_defs
from project_ask_ai_dagster.defs.ingestion import github_discussions_raw, github_issues_raw

defs: dg.Definitions = _raw_defs() if not isinstance(_raw_defs, dg.Definitions) else _raw_defs


def test_defs_load():
    assert isinstance(defs, dg.Definitions)


def test_assets_defined():
    repo = defs.get_repository_def()
    assert len(repo.assets_defs_by_key) > 0


def _make_mock_github(documents: list[Document]) -> MagicMock:
    mock_github = MagicMock()
    mock_github.get_issues.return_value = [{"id": "issue-1", "title": "Test Issue"}]
    mock_github.get_discussions.return_value = [{"id": "disc-1", "title": "Test Discussion"}]
    mock_github.convert_issues_to_documents.return_value = documents
    mock_github.convert_discussions_to_documents.return_value = documents
    return mock_github


def test_github_issues_raw_returns_documents():
    expected_docs = [
        Document(page_content="Issue content 1", metadata={"source": "github_issue"}),
        Document(page_content="Issue content 2", metadata={"source": "github_issue"}),
    ]
    mock_github = _make_mock_github(expected_docs)

    context = dg.build_asset_context(partition_key="2023-01-02")
    result = github_issues_raw(context, mock_github)

    assert result == expected_docs
    mock_github.get_issues.assert_called_once()


def test_github_issues_raw_passes_partition_window_to_resource():
    mock_github = _make_mock_github([])

    context = dg.build_asset_context(partition_key="2023-03-06")
    github_issues_raw(context, mock_github)

    call_kwargs = mock_github.get_issues.call_args.kwargs
    assert "start_date" in call_kwargs
    assert "end_date" in call_kwargs
    assert call_kwargs["start_date"] < call_kwargs["end_date"]


def test_github_discussions_raw_returns_documents():
    expected_docs = [
        Document(page_content="Discussion content", metadata={"source": "github_discussion"}),
    ]
    mock_github = _make_mock_github(expected_docs)

    context = dg.build_asset_context(partition_key="2023-01-02")
    result = github_discussions_raw(context, mock_github)

    assert result == expected_docs
    mock_github.get_discussions.assert_called_once()


def test_github_discussions_raw_converts_discussions():
    raw_discussions = [{"id": "d1"}, {"id": "d2"}]
    converted = [Document(page_content=f"doc {i}") for i in range(2)]

    mock_github = MagicMock()
    mock_github.get_discussions.return_value = raw_discussions
    mock_github.convert_discussions_to_documents.return_value = converted

    context = dg.build_asset_context(partition_key="2023-01-02")
    result = github_discussions_raw(context, mock_github)

    mock_github.convert_discussions_to_documents.assert_called_once_with(raw_discussions)
    assert result == converted
