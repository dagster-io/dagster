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
    class MyVerifiableResoruce(ConfigurableResource, ConfigVerifiable):
        a_str: str

        def verify_config(self) -> VerificationResult:
            if self.a_str == "foo":
                return VerificationResult(VerificationStatus.SUCCESS, "asdf")
            else:
                return VerificationResult(VerificationStatus.FAILURE, "qwer")

    defs = Definitions(
        resources={
            "my_resource": MyVerifiableResoruce(a_str="foo"),
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
            "my_resource": MyVerifiableResoruce(a_str="bar"),
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
    class MyVerifiableResoruce(ConfigurableResource, ConfigVerifiable):
        a_str: str

        def verify_config(self) -> VerificationResult:
            if self.a_str == "foo":
                return VerificationResult(VerificationStatus.SUCCESS, "asdf")
            else:
                return VerificationResult(VerificationStatus.FAILURE, "qwer")

    defs = Definitions(
        resources={
            "my_resource": MyVerifiableResoruce(a_str=EnvVar("ENV_VARIABLE_FOR_TEST")),
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
