from dagster import (
    ConfigurableResource,
    Definitions,
    EnvVar,
    ReadinessCheckedResource,
    ReadinessCheckResult,
    ReadinessCheckStatus,
)
from dagster._config.structured_config.readiness_check import (
    launch_resource_readiness_check,
)
from dagster._core.instance_for_test import instance_for_test
from dagster._core.test_utils import environ


def test_config_readiness_checked_basic() -> None:
    class FailureToggleReadinessCheckedResource(ConfigurableResource, ReadinessCheckedResource):
        should_pass_readiness_check: bool

        def readiness_check(self) -> ReadinessCheckResult:
            if self.should_pass_readiness_check:
                return ReadinessCheckResult.success("asdf")
            else:
                return ReadinessCheckResult.failure("qwer")

    defs = Definitions(
        resources={
            "my_resource": FailureToggleReadinessCheckedResource(should_pass_readiness_check=True),
        },
    )

    with instance_for_test() as instance:
        output = launch_resource_readiness_check(
            defs.get_repository_def(), instance.get_ref(), "my_resource"
        ).response

        assert output.status == ReadinessCheckStatus.SUCCESS
        assert output.message == "asdf"

    defs = Definitions(
        resources={
            "my_resource": FailureToggleReadinessCheckedResource(should_pass_readiness_check=False),
        },
    )

    with instance_for_test() as instance:
        output = launch_resource_readiness_check(
            defs.get_repository_def(), instance.get_ref(), "my_resource"
        ).response

        assert output.status == ReadinessCheckStatus.FAILURE
        assert output.message == "qwer"


def test_config_readiness_checked_env_var() -> None:
    class FailureToggleReadinessCheckedResource(ConfigurableResource, ReadinessCheckedResource):
        succeed_if_foo: str

        def readiness_check(self) -> ReadinessCheckResult:
            if self.succeed_if_foo == "foo":
                return ReadinessCheckResult.success("asdf")
            else:
                return ReadinessCheckResult.failure("qwer")

    defs = Definitions(
        resources={
            "my_resource": FailureToggleReadinessCheckedResource(
                succeed_if_foo=EnvVar("ENV_VARIABLE_FOR_TEST")
            ),
        },
    )
    with environ(
        {
            "ENV_VARIABLE_FOR_TEST": "foo",
        }
    ):
        with instance_for_test() as instance:
            output = launch_resource_readiness_check(
                defs.get_repository_def(), instance.get_ref(), "my_resource"
            ).response

            assert output.status == ReadinessCheckStatus.SUCCESS
            assert output.message == "asdf"

    with environ(
        {
            "ENV_VARIABLE_FOR_TEST": "bar",
        }
    ):
        with instance_for_test() as instance:
            output = launch_resource_readiness_check(
                defs.get_repository_def(), instance.get_ref(), "my_resource"
            ).response

            assert output.status == ReadinessCheckStatus.FAILURE
            assert output.message == "qwer"
