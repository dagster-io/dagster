"""Which failures are the caller's fault and which are ours.

Callers branch on `DagsterPlusClientError` vs `DagsterPlusServerError` to decide whether a
failure is worth alerting on, so the class each typename maps to is a contract rather than
an implementation detail. Everything still subclasses `DagsterPlusGraphqlError`, so these
assert the specific class rather than the base.
"""

import re
from pathlib import Path
from unittest.mock import Mock

import dagster_rest_resources.api
import pytest
from dagster_rest_resources.__generated__.get_issue import GetIssue, GetIssueIssueUnauthorizedError
from dagster_rest_resources.__generated__.get_run import (
    GetRun,
    GetRunRunOrErrorPythonError,
    GetRunRunOrErrorRunNotFoundError,
)
from dagster_rest_resources.__generated__.list_asset_checks import (
    ListAssetChecks,
    ListAssetChecksAssetNodeOrErrorAssetNode,
    ListAssetChecksAssetNodeOrErrorAssetNodeAssetChecksOrErrorAssetCheckNeedsMigrationError,
)
from dagster_rest_resources.__generated__.list_runs import (
    ListRuns,
    ListRunsRunsOrErrorInvalidPipelineRunsFilterError,
)
from dagster_rest_resources.__generated__.terminate_run import (
    TerminateRun,
    TerminateRunTerminateRunTerminateRunFailure,
)
from dagster_rest_resources.api.asset_check import DgApiAssetCheckApi
from dagster_rest_resources.api.issue import DgApiIssueApi
from dagster_rest_resources.api.run import DgApiRunApi
from dagster_rest_resources.gql_client import IGraphQLClient
from dagster_rest_resources.schemas.exception import (
    _TYPENAME_ERRORS,
    DagsterPlusClientError,
    DagsterPlusGraphqlError,
    DagsterPlusServerError,
    DagsterPlusUnauthorizedError,
    error_for_typename,
)


class TestHierarchy:
    def test_unauthorized_is_a_client_error(self):
        # The only client error with its own class, because callers were catching it by name
        # before the split and it carries a distinct message.
        assert issubclass(DagsterPlusUnauthorizedError, DagsterPlusClientError)
        assert not issubclass(DagsterPlusUnauthorizedError, DagsterPlusServerError)

    def test_client_and_server_faults_are_disjoint(self):
        assert not issubclass(DagsterPlusClientError, DagsterPlusServerError)

    def test_server_faults_are_not_client_errors(self):
        assert not issubclass(DagsterPlusServerError, DagsterPlusClientError)

    @pytest.mark.parametrize("error_type", [DagsterPlusClientError, DagsterPlusServerError])
    def test_existing_handlers_still_match(self, error_type):
        # Consumers catching the old flat type must keep catching everything.
        assert issubclass(error_type, DagsterPlusGraphqlError)


class TestErrorForTypename:
    def test_python_error_is_a_server_fault(self):
        assert error_for_typename("PythonError") is DagsterPlusServerError

    def test_unknown_typename_is_a_server_fault(self):
        # A union member we do not handle yet should stay visible, not be blamed on the caller.
        assert error_for_typename("SomeFutureError") is DagsterPlusServerError

    def test_known_typenames_map_to_their_class(self):
        assert error_for_typename("RunNotFoundError") is DagsterPlusClientError
        assert error_for_typename("UnauthorizedError") is DagsterPlusUnauthorizedError


class TestApiRaisesClassifiedErrors:
    def test_missing_run_is_a_caller_fault(self):
        client = Mock(spec=IGraphQLClient)
        client.get_run.return_value = GetRun(
            runOrError=GetRunRunOrErrorRunNotFoundError(
                __typename="RunNotFoundError", runId="run-xyz", message=""
            )
        )
        with pytest.raises(DagsterPlusClientError):
            DgApiRunApi(client).get_run("run-xyz")

    def test_backend_exception_is_a_server_fault(self):
        client = Mock(spec=IGraphQLClient)
        client.get_run.return_value = GetRun(
            runOrError=GetRunRunOrErrorPythonError(__typename="PythonError", message="", stack=[])
        )
        with pytest.raises(DagsterPlusServerError):
            DgApiRunApi(client).get_run("run-xyz")

    def test_bad_filter_is_a_caller_fault(self):
        client = Mock(spec=IGraphQLClient)
        client.list_runs.return_value = ListRuns(
            runsOrError=ListRunsRunsOrErrorInvalidPipelineRunsFilterError(
                __typename="InvalidPipelineRunsFilterError",
                message="pipelineName is not a valid filter",
            )
        )
        with pytest.raises(DagsterPlusClientError):
            DgApiRunApi(client).list_runs()

    def test_terminating_a_finished_run_is_a_caller_fault(self):
        client = Mock(spec=IGraphQLClient)
        client.terminate_run.return_value = TerminateRun(
            terminateRun=TerminateRunTerminateRunTerminateRunFailure(
                __typename="TerminateRunFailure", message="already finished"
            )
        )
        with pytest.raises(DagsterPlusClientError):
            DgApiRunApi(client).action_terminate_run("run-1")

    def test_no_permission_is_unauthorized(self):
        client = Mock(spec=IGraphQLClient)
        client.get_issue.return_value = GetIssue(
            issue=GetIssueIssueUnauthorizedError(__typename="UnauthorizedError", message="")
        )
        with pytest.raises(DagsterPlusUnauthorizedError):
            DgApiIssueApi(_client=client).get_issue("")

    def test_stale_deployment_is_a_caller_fault(self):
        client = Mock(spec=IGraphQLClient)
        client.list_asset_checks.return_value = ListAssetChecks(
            assetNodeOrError=ListAssetChecksAssetNodeOrErrorAssetNode(
                __typename="AssetNode",
                assetChecksOrError=ListAssetChecksAssetNodeOrErrorAssetNodeAssetChecksOrErrorAssetCheckNeedsMigrationError(
                    __typename="AssetCheckNeedsMigrationError", message="run a migration"
                ),
            )
        )
        with pytest.raises(DagsterPlusClientError):
            DgApiAssetCheckApi(client).list_asset_checks("foo")


def _explicit_match_arms() -> list[tuple[str, int, str, str]]:
    """Every `case "<typename>": raise <ErrorClass>(` in the api package.

    Tracks the enclosing case by indentation, so a raise guarding a success arm (say
    `case "AssetConnection":` raising when the node list is empty) is attributed to
    "AssetConnection" rather than to whichever case was matched last.
    """
    api_dir = Path(dagster_rest_resources.api.__file__).parent
    arms: list[tuple[str, int, str, str]] = []
    for path in sorted(api_dir.glob("*.py")):
        stack: list[tuple[int, str]] = []
        for lineno, raw in enumerate(path.read_text().splitlines(), 1):
            stripped = raw.strip()
            if not stripped:
                continue
            indent = len(raw) - len(raw.lstrip())
            while stack and stack[-1][0] >= indent:
                stack.pop()
            case_match = re.match(r"case (.+?):\s*$", stripped)
            if case_match:
                stack.append((indent, case_match.group(1)))
                continue
            raise_match = re.match(r"raise (DagsterPlus\w+)\(", stripped)
            if not raise_match or not stack:
                continue
            label = stack[-1][1]
            if label.startswith('"'):
                arms.append((path.name, lineno, label.strip('"'), raise_match.group(1)))
    return arms


class TestArmsAgreeWithTypenameMap:
    """The api modules classify inline while the catch-alls call `error_for_typename`.

    Two representations of the same decision can drift, so this pins them together: a
    typename raised inline must match what the map says for it.
    """

    def test_finds_the_match_arms(self):
        # Without this the parser could silently match nothing and the check below would pass.
        arms = _explicit_match_arms()
        assert len(arms) >= 50
        assert len({module for module, _, _, _ in arms}) >= 5

    def test_no_arm_contradicts_the_map(self):
        mismatched = [
            f"{module}:{lineno} case {typename!r} raises {raised}, "
            f"map says {error_for_typename(typename).__name__}"
            for module, lineno, typename, raised in _explicit_match_arms()
            # Typenames absent from the map are success arms whose guards raise.
            if typename in _TYPENAME_ERRORS and raised != error_for_typename(typename).__name__
        ]
        assert not mismatched, "\n".join(mismatched)
