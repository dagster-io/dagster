import mock
from dagster.core.errors import DagsterRunAlreadyExists
from dagster.core.test_utils import instance_for_test, register_managed_run_for_test


class Spy:
    def __init__(self, func):
        self.func = func
        self.return_values = []
        self.exceptions = []

    def __call__(self, *args, **kwargs):
        try:
            answer = self.func(*args, **kwargs)
            self.return_values.append(answer)
            return answer
        except DagsterRunAlreadyExists:
            self.exceptions = [DagsterRunAlreadyExists]
            raise DagsterRunAlreadyExists


# See comment for fn register_managed_run().
# Test the case where:
# 1. Multiple callers invoke register_managed_run() simultaneously for the same run.
# 2. Both receive has_run() is False. See: (*)
# 3. Both try to add_run(), with the first succeeding. We expect the second to receive
#    DagsterRunAlreadyExists exception.
# 4. We expect the second to then try to get_run() again, this time succeeding.
# 5. We expect the run storage to only contain one run.
def test_pipeline_run_creation_race():
    with instance_for_test() as instance:
        run_id = "run_id"

        # Spy on the result of add_run
        add_run_spy = Spy(instance._run_storage.add_run)  # pylint: disable=protected-access
        add_run_mock = mock.MagicMock(side_effect=add_run_spy)
        instance._run_storage.add_run = add_run_mock  # pylint: disable=protected-access

        # This invocation should successfully add the run to run storage
        pipeline_run = register_managed_run_for_test(instance, run_id=run_id)
        assert len(add_run_mock.call_args_list) == 1
        assert instance.has_run(run_id)

        # Check that add_run did not receive DagsterRunAlreadyExists exception and that
        # it successfully returned
        assert add_run_spy.exceptions == []
        assert len(add_run_spy.return_values) == 1

        # (*) Simulate a race where second invocation receives has_run() is False
        fetched_pipeline_run = ""
        with mock.patch.object(instance, "has_run", mock.MagicMock(return_value=False)):
            fetched_pipeline_run = register_managed_run_for_test(instance, run_id=run_id)

        # Check that add_run received DagsterRunAlreadyExists exception and did not return value
        assert len(add_run_mock.call_args_list) == 2
        assert add_run_spy.exceptions == [DagsterRunAlreadyExists]
        assert len(add_run_spy.return_values) == 1

        assert pipeline_run == fetched_pipeline_run
        assert instance.has_run(run_id)
        assert len(instance.get_runs()) == 1
