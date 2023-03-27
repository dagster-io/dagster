from typing import cast

from dagster import (
    ConfigurableResource,
    ConfigVerifiable,
    Definitions,
    EnvVar,
    VerificationResult,
    VerificationStatus,
)
from dagster._config.structured_config.resource_verification import (
    resource_verification_job_name,
    resource_verification_op_name,
)
from dagster._core.test_utils import environ


def test_config_verifiable_job_basic() -> None:
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

    job_names = {j.name for j in defs.get_all_job_defs()}
    verification_job_name = resource_verification_job_name("my_resource")

    assert verification_job_name in job_names, "Expected verification job to be created"
    verification_job = defs.get_job_def(resource_verification_job_name("my_resource"))

    result = verification_job.execute_in_process()
    assert result.success

    output = cast(
        VerificationResult, result.output_for_node(resource_verification_op_name("my_resource"))
    )
    assert output.status == VerificationStatus.SUCCESS
    assert output.message == "asdf"

    defs = Definitions(
        resources={
            "my_resource": FailureToggleVerificableResource(should_pass_verification=False),
        },
    )

    job_names = {j.name for j in defs.get_all_job_defs()}
    verification_job_name = resource_verification_job_name("my_resource")

    assert verification_job_name in job_names, "Expected verification job to be created"
    verification_job = defs.get_job_def(resource_verification_job_name("my_resource"))

    result = verification_job.execute_in_process()
    assert result.success

    output = cast(
        VerificationResult, result.output_for_node(resource_verification_op_name("my_resource"))
    )
    assert output.status == VerificationStatus.FAILURE
    assert output.message == "qwer"


def test_config_verifiable_job_env_var() -> None:
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

    job_names = {j.name for j in defs.get_all_job_defs()}
    verification_job_name = resource_verification_job_name("my_resource")

    assert verification_job_name in job_names, "Expected verification job to be created"
    verification_job = defs.get_job_def(resource_verification_job_name("my_resource"))

    with environ(
        {
            "ENV_VARIABLE_FOR_TEST": "foo",
        }
    ):
        result = verification_job.execute_in_process()
        assert result.success

        output = cast(
            VerificationResult, result.output_for_node(resource_verification_op_name("my_resource"))
        )
        assert output.status == VerificationStatus.SUCCESS
        assert output.message == "asdf"

    with environ(
        {
            "ENV_VARIABLE_FOR_TEST": "bar",
        }
    ):
        result = verification_job.execute_in_process()
        assert result.success

        output = cast(
            VerificationResult, result.output_for_node(resource_verification_op_name("my_resource"))
        )
        assert output.status == VerificationStatus.FAILURE
        assert output.message == "qwer"
