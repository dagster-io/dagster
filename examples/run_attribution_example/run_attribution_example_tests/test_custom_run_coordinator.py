import pytest
from dagster.core.run_coordinator import SubmitRunContext
from dagster.core.storage.dagster_run import DagsterRunStatus
from dagster_tests.core_tests.run_coordinator_tests.test_queued_run_coordinator import (
    TestQueuedRunCoordinator,
)
from mock import patch
from run_attribution_example.custom_run_coordinator import CustomRunCoordinator


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
        with patch(
            "run_attribution_example.custom_run_coordinator.has_request_context"
        ) as mock_has_request_context, patch(
            "run_attribution_example.custom_run_coordinator.warnings"
        ) as mock_warnings:
            mock_has_request_context.return_value = False

            run = self.create_run(
                instance,
                external_pipeline,
                run_id=run_id,
                status=DagsterRunStatus.NOT_STARTED,
            )
            returned_run = coordinator.submit_run(SubmitRunContext(run, workspace))

            assert returned_run.run_id == run_id
            assert returned_run.status == DagsterRunStatus.QUEUED
            tags = instance.get_run_tags()
            assert len(tags) == 0
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
        with patch(
            "run_attribution_example.custom_run_coordinator.has_request_context"
        ) as mock_has_request_context, patch(
            "run_attribution_example.custom_run_coordinator.request",
            headers={
                "X-Amzn-Trace-Id": "some_info",
                "X-Amzn-Oidc-Data": jwt_header,
            },
        ):
            mock_has_request_context.return_value = True

            run = self.create_run(
                instance,
                external_pipeline,
                run_id=run_id,
                status=DagsterRunStatus.NOT_STARTED,
            )
            returned_run = coordinator.submit_run(SubmitRunContext(run, workspace))

            assert returned_run.run_id == run_id
            assert returned_run.status == DagsterRunStatus.QUEUED
            tags = instance.get_run_tags()
            assert len(tags) == 1
            (tag_name, set_of_tag_values) = tags[0]
            assert tag_name == "user"
            assert set_of_tag_values == {expected_email}
