"""Unit tests for error handling in scaffold branch functionality."""

import json
from unittest.mock import Mock, patch

import pytest
from dagster_dg_core.context import DgContext
from dagster_dg_core.utils import ensure_dagster_dg_tests_import

ensure_dagster_dg_tests_import()

from dagster_dg_cli.cli.scaffold.branch import (
    TextInputType,
    get_branch_name_and_pr_title_from_prompt,
)


class TestGetBranchNameAndPrTitleFromPromptErrorHandling:
    """Test error handling in get_branch_name_and_pr_title_from_prompt function."""

    @patch("dagster_dg_cli.cli.scaffold.branch.run_claude")
    def test_json_decode_error_handling(self, mock_run_claude):
        """Test that JSONDecodeError is properly handled with descriptive error message."""
        # Mock run_claude to return non-JSON output
        mock_run_claude.return_value = "This is not valid JSON output"

        dg_context = Mock(spec=DgContext)
        user_input = "test prompt"
        input_type = TextInputType()

        with pytest.raises(RuntimeError) as exc_info:
            get_branch_name_and_pr_title_from_prompt(dg_context, user_input, input_type)

        error_msg = str(exc_info.value)
        assert "Failed to parse Claude output as JSON" in error_msg
        assert "Raw output was: 'This is not valid JSON output'" in error_msg
        assert "Expecting value: line 1 column 1 (char 0)" in error_msg

    @patch("dagster_dg_cli.cli.scaffold.branch.run_claude")
    def test_json_decode_error_with_partial_json(self, mock_run_claude):
        """Test JSON parsing error with partially valid JSON."""
        # Mock run_claude to return malformed JSON
        mock_run_claude.return_value = '{"branch-name": "test-branch", "pr-title":'

        dg_context = Mock(spec=DgContext)
        user_input = "test prompt"
        input_type = TextInputType()

        with pytest.raises(RuntimeError) as exc_info:
            get_branch_name_and_pr_title_from_prompt(dg_context, user_input, input_type)

        error_msg = str(exc_info.value)
        assert "Failed to parse Claude output as JSON" in error_msg
        assert 'Raw output was: \'{"branch-name": "test-branch", "pr-title":\'' in error_msg

    @patch("dagster_dg_cli.cli.scaffold.branch.run_claude")
    def test_missing_branch_name_field(self, mock_run_claude):
        """Test error when branch-name field is missing from Claude output."""
        # Mock run_claude to return JSON without branch-name field
        mock_run_claude.return_value = json.dumps({"pr-title": "Test PR Title"})

        dg_context = Mock(spec=DgContext)
        user_input = "test prompt"
        input_type = TextInputType()

        with pytest.raises(RuntimeError) as exc_info:
            get_branch_name_and_pr_title_from_prompt(dg_context, user_input, input_type)

        error_msg = str(exc_info.value)
        assert "Claude output missing required fields 'branch-name' or 'pr-title'" in error_msg
        assert 'Raw output was: \'{"pr-title": "Test PR Title"}\'' in error_msg

    @patch("dagster_dg_cli.cli.scaffold.branch.run_claude")
    def test_missing_pr_title_field(self, mock_run_claude):
        """Test error when pr-title field is missing from Claude output."""
        # Mock run_claude to return JSON without pr-title field
        mock_run_claude.return_value = json.dumps({"branch-name": "test-branch"})

        dg_context = Mock(spec=DgContext)
        user_input = "test prompt"
        input_type = TextInputType()

        with pytest.raises(RuntimeError) as exc_info:
            get_branch_name_and_pr_title_from_prompt(dg_context, user_input, input_type)

        error_msg = str(exc_info.value)
        assert "Claude output missing required fields 'branch-name' or 'pr-title'" in error_msg
        assert 'Raw output was: \'{"branch-name": "test-branch"}\'' in error_msg

    @patch("dagster_dg_cli.cli.scaffold.branch.run_claude")
    def test_missing_both_fields(self, mock_run_claude):
        """Test error when both required fields are missing from Claude output."""
        # Mock run_claude to return JSON without required fields
        mock_run_claude.return_value = json.dumps({"other-field": "some value"})

        dg_context = Mock(spec=DgContext)
        user_input = "test prompt"
        input_type = TextInputType()

        with pytest.raises(RuntimeError) as exc_info:
            get_branch_name_and_pr_title_from_prompt(dg_context, user_input, input_type)

        error_msg = str(exc_info.value)
        assert "Claude output missing required fields 'branch-name' or 'pr-title'" in error_msg
        assert 'Raw output was: \'{"other-field": "some value"}\'' in error_msg

    @patch("dagster_dg_cli.cli.scaffold.branch.run_claude")
    def test_empty_json_object(self, mock_run_claude):
        """Test error when Claude returns empty JSON object."""
        # Mock run_claude to return empty JSON object
        mock_run_claude.return_value = json.dumps({})

        dg_context = Mock(spec=DgContext)
        user_input = "test prompt"
        input_type = TextInputType()

        with pytest.raises(RuntimeError) as exc_info:
            get_branch_name_and_pr_title_from_prompt(dg_context, user_input, input_type)

        error_msg = str(exc_info.value)
        assert "Claude output missing required fields 'branch-name' or 'pr-title'" in error_msg
        assert "Raw output was: '{}'" in error_msg

    @patch("dagster_dg_cli.cli.scaffold.branch.run_claude")
    def test_successful_parsing(self, mock_run_claude):
        """Test successful parsing when all required fields are present."""
        # Mock run_claude to return valid JSON with all required fields
        expected_branch = "feature-test-branch"
        expected_title = "Add test feature"
        mock_run_claude.return_value = json.dumps(
            {"branch-name": expected_branch, "pr-title": expected_title}
        )

        dg_context = Mock(spec=DgContext)
        user_input = "test prompt"
        input_type = TextInputType()

        branch_name, pr_title = get_branch_name_and_pr_title_from_prompt(
            dg_context, user_input, input_type
        )

        assert branch_name == expected_branch
        assert pr_title == expected_title

    @patch("dagster_dg_cli.cli.scaffold.branch.run_claude")
    def test_valid_json_with_extra_fields(self, mock_run_claude):
        """Test that extra fields in JSON don't cause issues."""
        # Mock run_claude to return valid JSON with extra fields
        expected_branch = "feature-branch"
        expected_title = "Feature PR"
        mock_run_claude.return_value = json.dumps(
            {
                "branch-name": expected_branch,
                "pr-title": expected_title,
                "extra-field": "ignored",
                "another-field": 123,
            }
        )

        dg_context = Mock(spec=DgContext)
        user_input = "test prompt"
        input_type = TextInputType()

        branch_name, pr_title = get_branch_name_and_pr_title_from_prompt(
            dg_context, user_input, input_type
        )

        assert branch_name == expected_branch
        assert pr_title == expected_title
