from unittest import mock

import pytest
from dagster._core.errors import DagsterInvariantViolationError
from dagster_graphql.implementation.execution.backfill import create_and_launch_partition_backfill


def test_stop_protocol_rejects_synchronous_submission_before_run_creation():
    graphene_info = mock.Mock()
    graphene_info.context.instance.backfill_stop_protocol_enabled = True
    with pytest.raises(DagsterInvariantViolationError, match="forceSynchronousSubmission"):
        create_and_launch_partition_backfill(graphene_info, {"forceSynchronousSubmission": True})
    graphene_info.context.instance.add_backfill.assert_not_called()
    graphene_info.context.instance.create_run.assert_not_called()
    graphene_info.context.get_partition_sets.assert_not_called()
