from dagster import (
    ConfigurableResource,
    ConfigVerifiable,
    Definitions,
    EnvVar,
    VerificationResult,
    VerificationStatus,
)
from dagster._config.structured_config.resource_verification import (
    launch_resource_verification,
)
from dagster._core.instance_for_test import instance_for_test
from dagster._core.test_utils import environ


def test_config_verifiable_basic() -> None:
    class FailureToggleVerificableResource(ConfigurableResource, ConfigVerifiable):
        should_pass_verification: bool

        def verify_config(self) -> VerificationResult:
            if self.should_pass_verification:
                return VerificationResult.success("asdf")
            else:
                return VerificationResult.failure("qwer")

    defs = Definitions(
        resources={
            "my_resource": FailureToggleVerificableResource(should_pass_verification=True),
        },
    )

    with instance_for_test() as instance:
        output = launch_resource_verification(
            defs.get_repository_def(), instance.get_ref(), "my_resource"
        ).response

        assert output.status == VerificationStatus.SUCCESS
        assert output.message == "asdf"

    defs = Definitions(
        resources={
            "my_resource": FailureToggleVerificableResource(should_pass_verification=False),
        },
    )

    with instance_for_test() as instance:
        output = launch_resource_verification(
            defs.get_repository_def(), instance.get_ref(), "my_resource"
        ).response

        assert output.status == VerificationStatus.FAILURE
        assert output.message == "qwer"


def test_config_verifiable_env_var() -> None:
    class FailureToggleVerifiableResource(ConfigurableResource, ConfigVerifiable):
        succeed_if_foo: str

        def verify_config(self) -> VerificationResult:
            if self.succeed_if_foo == "foo":
                return VerificationResult.success("asdf")
            else:
                return VerificationResult.failure("qwer")

    defs = Definitions(
        resources={
            "my_resource": FailureToggleVerifiableResource(
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
            output = launch_resource_verification(
                defs.get_repository_def(), instance.get_ref(), "my_resource"
            ).response

            assert output.status == VerificationStatus.SUCCESS
            assert output.message == "asdf"

    with environ(
        {
            "ENV_VARIABLE_FOR_TEST": "bar",
        }
    ):
        with instance_for_test() as instance:
            output = launch_resource_verification(
                defs.get_repository_def(), instance.get_ref(), "my_resource"
            ).response

            assert output.status == VerificationStatus.FAILURE
            assert output.message == "qwer"
