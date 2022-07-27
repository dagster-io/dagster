from collections import namedtuple

import pytest
from dagster_tests.core_tests.run_coordinator_tests.test_queued_run_coordinator import (
    TestQueuedRunCoordinator,
)
from mock import patch
from run_attribution_example.custom_run_coordinator import CustomRunCoordinator

from dagster._core.run_coordinator import SubmitRunContext
from dagster._core.storage.pipeline_run import PipelineRunStatus


class TestCustomRunCoordinator(TestQueuedRunCoordinator):
    @pytest.fixture(scope="function")
    def coordinator(self, instance):
        coordinator = CustomRunCoordinator()
        coordinator.register_instance(instance)
        yield coordinator

    def test_session_header_decode_failure(
        self, instance, coordinator, workspace, external_pipeline
    ):
        run_id = "foo-1"
        with patch("run_attribution_example.custom_run_coordinator.warnings") as mock_warnings:

            run = self.create_run(
                instance,
                external_pipeline,
                run_id=run_id,
                status=PipelineRunStatus.NOT_STARTED,
            )
            returned_run = coordinator.submit_run(SubmitRunContext(run, workspace))

            assert returned_run.run_id == run_id
            assert returned_run.status == PipelineRunStatus.QUEUED
            mock_warnings.warn.assert_called_once()
            assert mock_warnings.warn.call_args.args[0].startswith("Couldn't decode JWT header")

    def test_session_header_decode_success(
        self, instance, coordinator, workspace, external_pipeline
    ):
        run_id, jwt_header, expected_email = (
            "foo",
            "foo.eyJlbWFpbCI6ICJoZWxsb0BlbGVtZW50bC5jb20ifQ==.bar",
            "hello@elementl.com",
        )
        MockRequest = namedtuple("MockRequest", ["headers"])
        workspace._source = MockRequest(
            headers={
                "X-Amzn-Trace-Id": "some_info",
                "X-Amzn-Oidc-Data": jwt_header,
            }
        )

        run = self.create_run(
            instance,
            external_pipeline,
            run_id=run_id,
            status=PipelineRunStatus.NOT_STARTED,
        )
        returned_run = coordinator.submit_run(SubmitRunContext(run, workspace))

        assert returned_run.run_id == run_id
        assert returned_run.status == PipelineRunStatus.QUEUED

        fetched_run = instance.get_run_by_id(run_id)
        assert len(fetched_run.tags) == 1
        assert fetched_run.tags["user"] == expected_email
