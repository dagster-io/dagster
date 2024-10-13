from typing import Optional

import pytest
from dagster import job, op
from dagster._config.pythonic_config import Config
from pydantic import ValidationError, validator


def test_validators_basic() -> None:
    # showcase that Pydantic validators work as expected

    class UserConfig(Config):
        name: str
        username: str

        @validator("name")
        def name_must_contain_space(cls, v):
            if " " not in v:
                raise ValueError("must contain a space")
            return v.title()

        @validator("username")
        def username_alphanumeric(cls, v):
            assert v.isalnum(), "must be alphanumeric"
            return v

    executed = {}

    @op
    def greet_user(config: UserConfig) -> None:
        print(f"Hello {config.name}!")  # noqa: T201
        executed["greet_user"] = True

    @job
    def greet_user_job() -> None:
        greet_user()

    # Ensure construction-time validation works
    UserConfig(name="Arthur Miller", username="arthur")
    with pytest.raises(ValidationError, match="must be alphanumeric"):
        UserConfig(name="Arthur Miller", username="arthur invalid")
    with pytest.raises(ValidationError, match="must contain a space"):
        UserConfig(name="Arthur", username="arthur")

    # Ensure execution-time validation works
    assert greet_user_job.execute_in_process(
        {"ops": {"greet_user": {"config": {"name": "Arthur Miller", "username": "arthur"}}}}
    ).success
    assert executed["greet_user"]

    executed.clear()
    with pytest.raises(ValidationError, match="must be alphanumeric"):
        greet_user_job.execute_in_process(
            {
                "ops": {
                    "greet_user": {
                        "config": {"name": "Arthur Miller", "username": "arthur invalid"}
                    }
                }
            }
        )
    assert not executed
    with pytest.raises(ValidationError, match="must contain a space"):
        greet_user_job.execute_in_process(
            {"ops": {"greet_user": {"config": {"name": "Arthur", "username": "arthur"}}}}
        )
    assert not executed


def test_validator_default_contract() -> None:
    # ensures Pydantic's validator decorator works as expected
    # in particular that it does not validate default values
    # but does validate any explicit inputs matching the default
    class UserConfig(Config):
        name: Optional[str] = None

        @validator("name")
        def name_must_not_be_provided(cls, name):
            raise ValueError("I always error with a non-default value!")

    UserConfig()
    with pytest.raises(ValidationError, match="I always error with a non-default value!"):
        UserConfig(name="Arthur Miller")
    with pytest.raises(ValidationError, match="I always error with a non-default value!"):
        UserConfig(name=None)


def test_validator_default_contract_nested() -> None:
    # as above, more complex case
    class InnerConfig(Config):
        name: Optional[str] = None

        @validator("name")
        def name_must_not_be_provided(cls, name):
            raise ValueError("Inner always errors with a non-default value!")

    class OuterConfig(Config):
        inner: InnerConfig
        name: Optional[str] = None

        @validator("name")
        def name_must_not_be_provided(cls, name):
            raise ValueError("Outer always errors with a non-default value!")

    OuterConfig(inner=InnerConfig())
    with pytest.raises(ValidationError, match="Outer always errors with a non-default value!"):
        OuterConfig(inner=InnerConfig(), name=None)
    with pytest.raises(ValidationError, match="Inner always errors with a non-default value!"):
        OuterConfig(inner=InnerConfig(name=None))

    executed = {}

    @op
    def my_op(config: OuterConfig) -> None:
        executed["my_op"] = True

    @job
    def my_job() -> None:
        my_op()

    assert my_job.execute_in_process().success
    assert executed["my_op"]
